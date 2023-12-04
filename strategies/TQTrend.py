from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.common.enums import LogColor
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.risk.sizing import FixedRiskSizer  as sizer
from indicators import tq
class TQTrendConfig(StrategyConfig, frozen=True):

  instrument_id: str
  bar_type: str
  trade_size: float = .02
  close_positions_on_stop: bool = True

class TQTrend(Strategy):
  def __init__(self, config: TQTrendConfig) -> None:
    super().__init__(config)
            
    self.instrument_id = InstrumentId.from_str(config.instrument_id)
    self.bar_type = BarType.from_str(config.bar_type)
    self.trade_size = sizer(config.trade_size)
    self.close_positions_on_stop = config.close_positions_on_stop
    self.instrument: Instrument = None

    self.tq = tq()
    
    self.close_positions_on_stop = config.close_positions_on_stop
    self.instrument: Instrument = None

  def on_start(self) -> None:
    self.instrument = self.cache.instrument(self.instrument_id)
    if self.instrument is None:
          self.log.error(f"Could not find instrument for {self.instrument_id}")
          self.stop()
          return

      # Register the indicators for updating
    self.register_indicator_for_bars(self.bar_type, self.tq)
    
    self.request_bars(self.bar_type, start=self._clock.utc_now() - pd.Timedelta(days=1))
    self.subscribe_bars(self.bar_type)
    
  def on_stop(self) -> None:
    pass
    
  def on_bar(self, bar: Bar) -> None:

    self.log.info(repr(bar), LogColor.CYAN)

    # Check if indicators ready
    if not self.indicators_initialized():
        self.log.info(
            f"Waiting for indicators to warm up [{self.cache.bar_count(self.bar_type)}]...",
            color=LogColor.BLUE,
        )
        return  # Wait for indicators to warm up...

    if bar.is_single_price():
        # Implies no market information for this bar
        return

    # BUY LOGIC
    if self.tq.value >= 5:
        if self.portfolio.is_flat(self.instrument_id):
            self.buy()
        elif self.portfolio.is_net_short(self.instrument_id):
            self.close_all_positions(self.instrument_id)
            self.buy()
    # SELL LOGIC
    elif self.tq.value <= -5:
        if self.portfolio.is_flat(self.instrument_id):
            self.sell()
        elif self.portfolio.is_net_long(self.instrument_id):
            self.close_all_positions(self.instrument_id)
            self.sell()

  def buy(self) -> None:

    order: MarketOrder = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=OrderSide.BUY,
        quantity=self.instrument.make_qty(self.trade_size),
        # time_in_force=TimeInForce.FOK,
    )

    self.submit_order(order)

  def sell(self) -> None:

      order: MarketOrder = self.order_factory.market(
          instrument_id=self.instrument_id,
          order_side=OrderSide.SELL,
          quantity=self.instrument.make_qty(self.trade_size),
          # time_in_force=TimeInForce.FOK,
      )

      self.submit_order(order)
  
  def on_stop(self) -> None:

    self.cancel_all_orders(self.instrument_id)
    if self.close_positions_on_stop:
        self.close_all_positions(self.instrument_id)

    self.unsubscribe_bars(self.bar_type)

  def on_reset(self) -> None:
    """
    Actions to be performed when the strategy is reset.
    """
    # Reset indicators here
    self.tq.reset()
