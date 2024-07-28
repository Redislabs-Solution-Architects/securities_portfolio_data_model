package com.bestarch.demo.service;

import java.time.Duration;
import java.util.Arrays;
import java.util.Map;

import org.apache.commons.pool2.impl.GenericObjectPool;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.stereotype.Component;

import com.bestarch.demo.domain.StockPriceStreamRecord;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.redis.lettucemod.api.StatefulRedisModulesConnection;
import com.redis.lettucemod.api.sync.RedisTimeSeriesCommands;
import com.redis.lettucemod.timeseries.AddOptions;
import com.redis.lettucemod.timeseries.Aggregator;
import com.redis.lettucemod.timeseries.CreateOptions;
import com.redis.lettucemod.timeseries.CreateRuleOptions;
import com.redis.lettucemod.timeseries.DuplicatePolicy;
import com.redis.lettucemod.timeseries.Sample;

import io.lettuce.core.KeyValue;
import io.lettuce.core.api.sync.RedisCommands;
import jakarta.annotation.PostConstruct;


@Component
public class StockPriceConsumer implements StreamListener<String, MapRecord<String, String, String>> {
	
	private Logger logger = LoggerFactory.getLogger(getClass());

	@Value("${price.update.stream}")
	private String priceUpdateStream;
	
	@Value("${timeseries.prefix}")
	private String PREFIX;
	
	@Value("${timeseries.stocks}")
	private String stocks;
	
	@Value("${timeseries.bucket}")
	private Integer BUCKETSIZE;
	
	RedisConnectionFactory redisConnectionFactory;
	
	private String priceUpdateGroup = "price_update_group";
	
	@Autowired
	private GenericObjectPool<StatefulRedisModulesConnection<String, String>> pool;

	private final static ObjectMapper objectMapper = new ObjectMapper();
	
	private static String KEY = "";

	@Override
	@SuppressWarnings("unchecked")
	public void onMessage(MapRecord<String, String, String> message) {
		StatefulRedisModulesConnection<String, String> connection = null;
		try {
			connection = pool.borrowObject();
			RedisTimeSeriesCommands<String, String> ts = connection.sync();
			Map<String, String> values = message.getValue();
			logger.info(values.toString());
			StockPriceStreamRecord rec = objectMapper.convertValue(values, StockPriceStreamRecord.class);
			KEY = PREFIX + rec.getTicker();
			ts.tsAdd(KEY, Sample.of(rec.getDateInUnix()*1000, rec.getPrice()), 
					AddOptions.<String, String>builder()
					.labels(KeyValue.just("type", "stock"))
					.policy(DuplicatePolicy.LAST)
					.build());
			
			RedisCommands<String, String> commands = connection.sync();
			commands.xack(priceUpdateStream, priceUpdateGroup, message.getId().getValue());
		} catch (Exception e) {
			logger.error("An exception occurred while consuming the message. Ignoring the error", e);
		} finally {
			try {
				pool.returnObject(connection);
			} catch (Exception exp) {
				logger.error("Exception occurred while returning connection to pool", exp);
			}
		}
	}
	
	@PostConstruct
	public void init() {
		try {
			String key = null;
			Duration bucketSize = Duration.ofSeconds(BUCKETSIZE);
			StatefulRedisModulesConnection<String, String> connection = pool.borrowObject();
			RedisTimeSeriesCommands<String, String> ts = connection.sync();
			String[] stockStr = stocks.split(",");
			for (String s:stockStr) {
				key = PREFIX + s;
				
				try {
					ts.tsCreate(key, CreateOptions.<String, String>builder()
							.labels(Arrays.asList(KeyValue.just("type", "stock")))
							.policy(DuplicatePolicy.LAST).build());
				} catch (Exception e) {
					logger.error("An error occurred while creating timeseries key {}", key);
				}
				
				ts.tsCreate(key + ":o", CreateOptions.<String, String>builder()
						.labels(Arrays.asList(KeyValue.just("type", "stock")))
						.policy(DuplicatePolicy.LAST).build());
				ts.tsCreaterule(key, key + ":o", CreateRuleOptions.builder(Aggregator.FIRST).bucketDuration(bucketSize).build());
				
				
				ts.tsCreate(key + ":c", CreateOptions.<String, String>builder()
						.labels(Arrays.asList(KeyValue.just("type", "stock")))
						.policy(DuplicatePolicy.LAST).build());
				ts.tsCreaterule(key, key + ":c", CreateRuleOptions.builder(Aggregator.LAST).bucketDuration(bucketSize).build());
				
				
				ts.tsCreate(key + ":h", CreateOptions.<String, String>builder()
						.labels(Arrays.asList(KeyValue.just("type", "stock")))
						.policy(DuplicatePolicy.LAST).build());
				ts.tsCreaterule(key, key + ":h", CreateRuleOptions.builder(Aggregator.MAX).bucketDuration(bucketSize).build());
				
				
				ts.tsCreate(key + ":l", CreateOptions.<String, String>builder()
						.labels(Arrays.asList(KeyValue.just("type", "stock")))
						.policy(DuplicatePolicy.LAST).build());
				ts.tsCreaterule(key, key + ":l", CreateRuleOptions.builder(Aggregator.MIN).bucketDuration(bucketSize).build());
			}
		} catch (Exception e) {
			logger.error("An error occurred while creating timeseries key OR rule");
		}
		
	}

}
