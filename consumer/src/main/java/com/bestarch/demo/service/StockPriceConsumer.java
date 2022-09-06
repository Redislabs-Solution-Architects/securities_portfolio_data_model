package com.bestarch.demo.service;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
	
	private Logger logger = LoggerFactory.getLogger(StockPriceConsumer.class);

	@Value("${price.update.stream}")
	private String priceUpdateStream;

	@Autowired
	private StatefulRedisModulesConnection<String, String> connection;

	private final static ObjectMapper objectMapper = new ObjectMapper();

	@Override
	public void onMessage(MapRecord<String, String, String> message) {
		try {
			RedisTimeSeriesCommands<String, String> ts = connection.sync();
			logger.info(message.toString());
			Map<String, String> values = message.getValue();
			StockPriceStreamRecord rec = objectMapper.convertValue(values, StockPriceStreamRecord.class);
			ts.tsAdd("price_history_ts:"+rec.getTicker(), Sample.of(rec.getDateInUnix(), rec.getPrice()));
		} catch (Exception e) {
			logger.error("An exception occurred in parsing. Ignoring the error", e);
		}
	}

}
