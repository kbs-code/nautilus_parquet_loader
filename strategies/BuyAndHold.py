from nautilus_trader.trading.strategy import Strategy, StrategyConfig
from nautilus_trader.model.enums import OrderSide

class BuyAndHoldConfig(StrategyConfig, frozen=True):

  instrument_id: str
  bar_type: str
  trade_size: float = 2.0
  close_positions_on_stop: bool = True

class BuyAndHold(Strategy):
  def __init__(self) -> None:
    super().__init__() 

  def on_start(self) -> None:
    self.instrument = self.cache.instrument(self.instrument_id)
    if self.instrument is None:
      self.log.error(f"Could not find instrument for {self.instrument_id}")
      self.stop()
      return

  def on_stop(self) -> None:
    self.close_all_positions()

  def on_bar(self) -> None:
    self.factory.market_order(
      instrument_id=self.instrument_id,
      side=OrderSide.BUY,
      quantity=1000,
      venue_id="SIM",
      )