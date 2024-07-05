package com.bestarch.demo;

import java.io.UnsupportedEncodingException;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;

import org.apache.commons.pool2.impl.GenericObjectPool;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import com.redis.lettucemod.api.StatefulRedisModulesConnection;
import com.redis.lettucemod.api.sync.RedisTimeSeriesCommands;
import com.redis.lettucemod.timeseries.Aggregator;
import com.redis.lettucemod.timeseries.CreateOptions;
import com.redis.lettucemod.timeseries.CreateRuleOptions;
import com.redis.lettucemod.timeseries.DuplicatePolicy;

import io.lettuce.core.KeyValue;

@SpringBootApplication
public class DemoApplication implements CommandLineRunner {
	
	@Autowired
	private GenericObjectPool<StatefulRedisModulesConnection<String, String>> pool;
	
	@Value("${timeseries.prefix}")
	private String PREFIX;
	
	@Value("${timeseries.stocks}")
	private String stocks;
	
	@Value("${timeseries.bucket}")
	private Integer BUCKETSIZE;

	private static Logger logger = LoggerFactory.getLogger(DemoApplication.class);

	public static void main(String[] args) throws NoSuchAlgorithmException, UnsupportedEncodingException {
		SpringApplication.run(DemoApplication.class, args);
		logger.info("Records will start processing");
		try {
			TimeUnit.SECONDS.sleep(2);
		} catch (InterruptedException e) {
		}
	}
	
	
	@Override
	public void run(String... args) throws Exception {
		String key = null;
		Duration bucketSize = Duration.ofSeconds(BUCKETSIZE);
		StatefulRedisModulesConnection<String, String> connection = pool.borrowObject();
		RedisTimeSeriesCommands<String, String> ts = connection.sync();
		String[] val = stocks.split(",");
		for (String s:val) {
			key = PREFIX + s;
			
			ts.tsCreate(key, CreateOptions.<String, String>builder()
					.labels(Arrays.asList(KeyValue.just("type", "stock")))
					.policy(DuplicatePolicy.LAST).build());
			
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
		
	}

}
