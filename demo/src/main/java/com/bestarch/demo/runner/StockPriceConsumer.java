package com.bestarch.demo.runner;

import java.io.UnsupportedEncodingException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Map;

import javax.annotation.PostConstruct;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.stereotype.Component;

import com.bestarch.demo.domain.StockPriceStreamRecord;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.redis.lettucemod.api.StatefulRedisModulesConnection;
import com.redis.lettucemod.api.sync.RedisTimeSeriesCommands;
import com.redis.lettucemod.timeseries.Sample;

@Component
public class StockPriceConsumer implements StreamListener<String, MapRecord<String, String, String>> {

	@Value("${price.update.stream}")
	private String priceUpdateStream;

	@Autowired
	private StatefulRedisModulesConnection<String, String> connection;

	private final static ObjectMapper objectMapper = new ObjectMapper();

	private SecureRandom random;

	@PostConstruct
	public void name() throws NoSuchAlgorithmException, UnsupportedEncodingException {
		random = SecureRandom.getInstance("SHA1PRNG");
		random.setSeed("ABC".getBytes("UTF-8"));
	}

	@Override
	public void onMessage(MapRecord<String, String, String> message) {
		RedisTimeSeriesCommands<String, String> ts = connection.sync();
		System.out.println(message);
		Map<String, String> values = message.getValue();
		try {
			StockPriceStreamRecord rec = objectMapper.convertValue(values, StockPriceStreamRecord.class);
			ts.tsAdd("price_history_ts:"+rec.getTicker(), Sample.of(rec.getDateInUnix(), rec.getPrice()));
		} catch (Exception e) {
			System.out.println("An exception occurred in parsing. Ignoring the error");
		}
		System.out.println();

	}

}
