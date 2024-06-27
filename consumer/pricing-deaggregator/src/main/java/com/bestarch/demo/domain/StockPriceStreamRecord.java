package com.bestarch.demo.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StockPriceStreamRecord {

	private String key;
	private String ticker;
	private String datetime;
	private Long dateInUnix;
	private Double price;

	@Override
	public String toString() {
		return "Record --> [key=" + key + ", ticker=" + ticker + ", datetime=" + datetime + ", dateInUnix=" + dateInUnix
				+ ", price=" + price + "]";
	}

}