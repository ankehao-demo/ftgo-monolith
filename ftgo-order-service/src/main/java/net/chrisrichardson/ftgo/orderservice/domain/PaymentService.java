package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.domain.PaymentInformation;

import java.util.UUID;

public class PaymentService {

    public PaymentInformation chargeCreditCard(long consumerId, Money orderTotal) {
        // In a real implementation, this would call a payment gateway (e.g., Stripe)
        // For now, generate a payment token to simulate a successful charge
        String paymentToken = UUID.randomUUID().toString();
        return new PaymentInformation(paymentToken);
    }
}
