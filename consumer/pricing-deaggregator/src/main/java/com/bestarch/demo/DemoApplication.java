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
import com.redis.lettucemod.timeseries.Sample;

import io.lettuce.core.KeyValue;

@SpringBootApplication
public class DemoApplication implements CommandLineRunner {
	
	@Value("${price.update.stream}")
	private String priceUpdateStream;
	
	@Value("${timeseries.prefix}")
	private String PREFIX;
	
	@Value("${timeseries.stocks}")
	private String stocks;
	
	@Value("${timeseries.bucket}")
	private Integer BUCKETSIZE;
	
	@Autowired
	private GenericObjectPool<StatefulRedisModulesConnection<String, String>> pool;
	
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
		Duration bucketSize = Duration.ofSeconds(BUCKETSIZE);
		StatefulRedisModulesConnection<String, String> connection = pool.borrowObject();
		RedisTimeSeriesCommands<String, String> ts = connection.sync();
		
//		ts.tsCreate("test", CreateOptions.<String, String>builder()
//				.labels(Arrays.asList(KeyValue.just("type", "stock")))
//				.policy(DuplicatePolicy.LAST).build());
//		
//		ts.tsCreate("test" + ":o", CreateOptions.<String, String>builder()
//				.labels(Arrays.asList(KeyValue.just("type", "stock")))
//				.build());
//		ts.tsCreaterule("test", "test" + ":o", CreateRuleOptions.builder(Aggregator.SUM).bucketDuration(bucketSize).build());
//		
//		for (int i=0;i<100;i++) {
//			TimeUnit.MILLISECONDS.sleep(1000);
//			long unixTime = System.currentTimeMillis();
//			ts.tsAdd("test", Sample.of(unixTime, i));
//		}
		//init();
		
	}
	
}
