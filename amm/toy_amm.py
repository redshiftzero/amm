import math

class Trade:
    def __init__(self, delta_a: int, delta_b: int):
        if delta_a > 0:
            self.delta_a = delta_a
        else:
            raise ValueError("delta_a must be positive")
        
        if delta_b > 0:
            self.delta_b = delta_b
        else:
            raise ValueError("delta_b must be positive")

class TradeBforA(Trade):
    """Represent a trade of delta_B coins B for delta_A coins A"""
    def __init__(self, delta_a: int, delta_b: int):
        super().__init__(delta_a, delta_b)

class TradeAforB(Trade):
    """Represent a trade of delta_A coins A for delta_B coins B"""
    def __init__(self, delta_a: int, delta_b: int):
        super().__init__(delta_a, delta_b)

class AMM:
    """Represents a zero-fee constant product market between two assets A and B"""
    def __init__(self, reserves_a: int, reserves_b: int):
        if reserves_a > 0:
            self.reserves_a = reserves_a
        else:
            raise ValueError("reserves of asset A must always be greater than 0")

        if reserves_b > 0:
            self.reserves_b = reserves_b
        else:
            raise ValueError("reserves of asset B must always be greater than 0")

        print('created AMM')
        self.constant_product = self.reserves_a * self.reserves_b
        print('constant product:', self.constant_product)

    def update_reserves(self, delta_a: int, delta_b: int) -> bool:
        """Update the reserves. Positive delta is adding reserves, negative is removing."""
        if self.reserves_a + delta_a <= 0:
            print('insufficient A')
            return False
        elif self.reserves_b + delta_b <= 0:
            print('insufficient B')
            return False
        else:
            self.reserves_a += delta_a
            self.reserves_b += delta_b
            print('new reserves of A:', self.reserves_a)
            print('new reserves of B:', self.reserves_b)
            print('constant product:', self.reserves_a * self.reserves_b)
            return True

    def price_oracle_asset_a(self) -> float:
        """Get current marginal price of asset A in B"""
        return self.reserves_a / self.reserves_b

    def price_oracle_asset_b(self) -> float:
        """Get current marginal price of asset B in A"""
        return self.reserves_b / self.reserves_a 

    def apply_trade(self, trade: Trade) -> bool:
        """See if trade is valid, if so execute and update the reserves"""
        if isinstance(trade, TradeAforB):
            if math.isclose((self.reserves_a + trade.delta_a) * (self.reserves_b - trade.delta_b), self.constant_product, abs_tol=0.1*self.constant_product) and \
                    self.update_reserves(trade.delta_a, -1 * trade.delta_b):
                print('trade executed')
                return True
            else:
                print('trade not executed')
                return False
        elif isinstance(trade, TradeBforA):
            if math.isclose((self.reserves_a - trade.delta_a) * (self.reserves_b + trade.delta_b), self.constant_product, abs_tol=0.1*self.constant_product) and \
                    self.update_reserves(-1 * trade.delta_a, trade.delta_b):
                print('trade executed')
                return True
            else:
                print('trade not executed')
                return False
        else:
            print('unknown trade type')
            return False


if __name__ == "__main__":
    market = AMM(100, 1000)
    print('current price of A:', market.price_oracle_asset_a())
    print('current price of B:', market.price_oracle_asset_b())

    valid_trade = TradeBforA(10, 1)
    assert market.apply_trade(valid_trade) == True

    invalid_trade = TradeBforA(1, 10)
    assert market.apply_trade(invalid_trade) == False
