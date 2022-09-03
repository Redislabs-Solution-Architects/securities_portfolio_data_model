package com.bestarch.demo.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.ToString;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@ToString
public class StockPriceStreamRecord {

	private String key;
	private String ticker;
	private String datetime;
	private Long dateInUnix;
	private Double price;
	
}