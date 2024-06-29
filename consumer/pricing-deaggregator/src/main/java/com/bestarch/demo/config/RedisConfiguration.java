package com.bestarch.demo.config;

import java.net.InetAddress;

import java.net.UnknownHostException;
import java.time.Duration;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.dao.DataAccessException;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisPassword;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.connection.stream.Consumer;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.RedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.data.redis.stream.StreamMessageListenerContainer;
import org.springframework.data.redis.stream.StreamMessageListenerContainer.StreamMessageListenerContainerOptions;
import org.springframework.data.redis.stream.Subscription;

import io.micrometer.core.instrument.util.StringUtils;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Configuration
class RedisConfiguration {
	
	private Logger logger = LoggerFactory.getLogger(getClass());

	@Value("${price.update.stream}")
	private String priceUpdateStream;
	
	private String priceUpdateGroup = "price_update_group";

	@Value("${spring.redis.host:localhost}")
	private String server;

	@Value("${spring.redis.port:6379}")
	private String port;

	@Value("${spring.redis.password}")
	private String pswd;

	@Autowired
	private StreamListener<String, MapRecord<String, String, String>> streamListener;

	@Bean
	public RedisConnectionFactory redisConnectionFactory() {
		RedisStandaloneConfiguration redisStandaloneConfiguration = new RedisStandaloneConfiguration(server,
				Integer.valueOf(port));
		if (StringUtils.isNotBlank(pswd)) {
			RedisPassword rp = RedisPassword.of(pswd);
			redisStandaloneConfiguration.setPassword(rp);
		} 
		return new LettuceConnectionFactory(redisStandaloneConfiguration);
	}
	
	@Bean
	public RedisTemplate<String, String> redisTemplate() {
		RedisTemplate<String, String> template = new RedisTemplate<>();
		RedisSerializer<String> stringSerializer = new StringRedisSerializer();

		template.setConnectionFactory(redisConnectionFactory());

		template.setKeySerializer(stringSerializer);
		template.setHashKeySerializer(stringSerializer);

		template.setValueSerializer(stringSerializer);
		template.setHashValueSerializer(stringSerializer);

		template.setEnableTransactionSupport(true);
		template.afterPropertiesSet();

		try {
			template.opsForStream().createGroup(priceUpdateStream, priceUpdateGroup);
		} catch (DataAccessException e) {
			logger.info("Ignoring the exception. Stream group 'priceUpdateStream' may be present already. Skipping it");
		}
		try {
			template.opsForStream().createGroup(priceUpdateStream, "stock_price_alert_group");
		} catch (DataAccessException e) {
			logger.info("Ignoring the exception. Stream group 'stock_price_alert_group' may be present already. Skipping it");
		}

		return template;
	}

	@Bean
	public Subscription subscription(RedisConnectionFactory redisConnectionFactory) throws UnknownHostException {

		StreamMessageListenerContainerOptions<String, MapRecord<String, String, String>> options = StreamMessageListenerContainer.StreamMessageListenerContainerOptions
				.builder().
				pollTimeout(Duration.ofSeconds(20))
				.serializer(new StringRedisSerializer())
				.build();

		StreamMessageListenerContainer<String, MapRecord<String, String, String>> listenerContainer = StreamMessageListenerContainer
				.create(redisConnectionFactory, options);

		Subscription subscription = listenerContainer.receiveAutoAck(
				Consumer.from(priceUpdateGroup, InetAddress.getLocalHost().getHostName()),
				StreamOffset.create(priceUpdateStream, ReadOffset.lastConsumed()), streamListener);
		listenerContainer.start();
		return subscription;
	}

}