"""Utilities to parse CME Span Risk Parameter Files."""

import datetime as dt

import cython


@cython.cclass
class String:
    start: cython.int
    stop: cython.int

    def __init__(self, start: cython.int, stop: cython.int):
        self.start = start
        self.stop = stop

    def __get__(self, obj, objtype) -> str:
        return str(obj[self.start : self.stop]).rstrip()


@cython.cclass
class Strings:
    start: cython.int
    stop: cython.int
    step: cython.int

    def __init__(self, start: cython.int, stop: cython.int, step: cython.int):
        self.start = start
        self.stop = stop
        self.step = step

    def __get__(self, obj, objtype) -> tuple[str, ...]:
        return tuple(
            str(obj[index : index + self.step]).rstrip()
            for index in range(self.start, self.stop, self.step)
        )


@cython.cclass
class Int:
    start: cython.int
    stop: cython.int

    def __init__(self, start: cython.int, stop: cython.int):
        self.start = start
        self.stop = stop

    def __get__(self, obj, objtype) -> int | None:
        try:
            return int(obj[self.start : self.stop])
        except ValueError:
            return None


@cython.cclass
class Float:
    start: cython.int
    stop: cython.int
    scale: cython.float

    def __init__(
        self,
        start: cython.int,
        stop: cython.int,
        scale: cython.float = 1e-6,
    ):
        self.start = start
        self.stop = stop
        self.scale = scale

    def __get__(self, obj, objtype) -> float:
        try:
            return int(obj[self.start : self.stop]) * (
                self.scale
                if self.scale < 0 and obj[self.stop] == "-"
                else abs(self.scale)
            )
        except ValueError:
            return float("nan")


@cython.cclass
class Date:
    start: cython.int

    def __init__(self, start: cython.int):
        self.start = start

    def __get__(self, obj, objtype) -> dt.date:
        return dt.datetime.strptime(obj[self.start : self.start + 8], r"%Y%m%d").date()


@cython.cclass
class Time:
    start: cython.int

    def __init__(self, start: cython.int):
        self.start = start

    def __get__(self, obj, objtype) -> dt.time:
        try:
            return dt.datetime.strptime(
                obj[self.start : self.start + 4], r"%H%M"
            ).time()
        except ValueError:
            return dt.time()


@cython.cclass
class Spans:
    start: cython.int
    stop: cython.int

    def __init__(self, start: cython.int, stop: cython.int):
        self.start = start
        self.stop = stop

    def __get__(self, obj, objtype) -> tuple[tuple[int, int], ...]:
        return tuple(
            (int(obj[index + 2 : index + 8]), int(obj[index + 8 : index + 14]))
            for index in range(self.start, self.stop, 14)
            if str(obj[index : index + 14]).isnumeric()
        )


@cython.cclass
class Risk:
    start: cython.int
    stop: cython.int

    def __init__(self, start: cython.int, stop: cython.int):
        self.start = start
        self.stop = stop

    def __get__(self, obj, objtype) -> tuple[float, ...]:
        return tuple(
            int(obj[index : index + 5]) * (-1e-4 if obj[index + 5] == "-" else 1e-4)
            for index in range(self.start, self.stop, 6)
        )


@cython.cclass
class Base(str):
    def __repr__(self) -> str:
        return "{name}({members})".format(
            name=self.__class__.__name__,
            members=", ".join(
                f"{key}={getattr(self, key)!r}"
                for key in sorted(set(dir(self)).difference(dir("")))
                if not key.startswith("__")
            ),
        )


@cython.cclass
class ExchangeComplexHeader(Base):
    """Exchange Complex Header (Record Type "0 ")

    >>> record("0 CME   20250620SE     202506201407U2YNCLR        C CUST  H HEDGE 1 CORE  M MAINT ")
    ExchangeComplexHeader(business_date=datetime.date(2025, 6, 20), business_time=datetime.time(0, 0), clearing_organization='CME', file_creation_date=datetime.date(2025, 6, 20), file_creation_time=datetime.time(14, 7), file_identifier='E', filler='CLR        C CUST  H HEDGE 1 CORE  M MAINT', format_indicator='U2', gross_net='N', overall_limit_option='Y', settlement_or_intraday='S')
    """

    clearing_organization = String(2, 8)
    business_date = Date(8)
    settlement_or_intraday = String(16, 17)
    file_identifier = String(17, 19)
    business_time = Time(19)
    file_creation_date = Date(23)
    file_creation_time = Time(31)
    format_indicator = String(35, 37)
    overall_limit_option = String(37, 38)
    gross_net = String(38, 39)
    filler = String(39, 132)


@cython.cclass
class CurrencyConversion(Base):
    """Currency Conversion Rates (Subrecord Type: "T ")

    >>> record("T CLPCUSD$0000001063")
    CurrencyConversion(from_code='C', from_iso='CLP', rate=0.001063, to_code='$', to_iso='USD')
    """

    from_iso = String(2, 5)
    from_code = String(5, 6)
    to_iso = String(6, 9)
    to_code = String(9, 10)
    rate = Float(10, 20)


@cython.cclass
class ExchangeHeader(Base):
    """First Combined Commodity Record (Record Type "1 ")

    >>> record("1 CBT  01")
    ExchangeHeader(acronym='CBT', code='01')
    """

    acronym = String(2, 5)
    code = String(7, 9)


@cython.cclass
class FirstCombinedCommodity(Base):
    """First Combined Commodity Report (Subrecord Type: "2 ")

    >>> record("2 CBT 26    0USD$PN   26        FUT   26        OOF   59        OOF   WT1       OOF   VT1       OOF   GT1       OOF")
    FirstCombinedCommodity(code='26', combination_margin_method='', commodity_1='26', commodity_2='26', commodity_3='59', commodity_4='WT1', commodity_5='VT1', commodity_6='GT1', contract_type_1='FUT', contract_type_2='OOF', contract_type_3='OOF', contract_type_4='OOF', contract_type_5='OOF', contract_type_6='OOF', echange='CBT', limit_option_value='N', option_margin_style='P', performance_bond_currency_code='$', performance_bond_currency_iso='USD')
    """

    echange = String(2, 5)
    code = String(6, 12)
    performance_bond_currency_iso = String(13, 16)
    performance_bond_currency_code = String(16, 17)
    option_margin_style = String(17, 18)  # [P]remium or [F]uture
    limit_option_value = String(18, 19)  # [Y]es or [N]o
    combination_margin_method = String(19, 20)  # [S]plit, [D]elta, or [M]odified split
    commodity_1 = String(22, 32)
    contract_type_1 = String(32, 35)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_2 = String(38, 48)
    contract_type_2 = String(48, 51)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_3 = String(54, 64)
    contract_type_3 = String(64, 67)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_4 = String(70, 80)
    contract_type_4 = String(80, 83)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_5 = String(86, 96)
    contract_type_5 = String(96, 99)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_6 = String(102, 112)
    contract_type_6 = String(112, 115)  # FUT, PHY, CMB, OOF, OOP, OOC


@cython.cclass
class SecondCombinedCommodity(Base):
    """Second Combined Commodity Record (Record Type: "3 ")

    >>> record("3 06    1001202507202507022025082025080320250920250904202510202511  100010001100")
    SecondCombinedCommodity(code='06', init_to_maint_hedger=1.0, init_to_maint_member=1.0, init_to_maint_speculator=1.1, spread_charge_method='10', tiers=((202507, 202507), (202508, 202508), (202509, 202509), (202510, 202511)))
    """

    code = String(2, 8)
    spread_charge_method = String(8, 10)
    tiers = Spans(10, 66)
    init_to_maint_member = Float(68, 72, scale=1e-3)
    init_to_maint_hedger = Float(72, 76, scale=1e-3)
    init_to_maint_speculator = Float(76, 80, scale=1e-3)


@cython.cclass
class ThirdCombinedCommodity(Base):
    """Third Combined Commodity Record (Record Type: "4 ")

    >>> record("4 YM    10010120250600000010000000                            00001701001001001")
    ThirdCombinedCommodity(adjustment_factor_hedgers=1.0, adjustment_factor_members=1.0, adjustment_factor_speculators=1.0, code='YM', delivery_month_1=1, delivery_month_1_charge_outrights=0.0, delivery_month_1_charge_spreads=1e-06, delivery_month_1_contract=202506, delivery_month_2=None, delivery_month_2_charge_outrights=nan, delivery_month_2_charge_spreads=nan, delivery_month_2_contract=None, number_of_spot_contracts=1, short_option_minimum_calculation_method=1, short_option_minimum_charge_rate=0.00016999999999999999, spot_charge_method=10)
    """

    code = String(2, 8)
    spot_charge_method = Int(8, 10)
    number_of_spot_contracts = Int(10, 12)
    delivery_month_1 = Int(12, 14)
    delivery_month_1_contract = Int(14, 20)
    delivery_month_1_charge_spreads = Float(20, 27)
    delivery_month_1_charge_outrights = Float(27, 34)
    delivery_month_2 = Int(34, 36)
    delivery_month_2_contract = Int(36, 42)
    delivery_month_2_charge_spreads = Float(42, 49)
    delivery_month_2_charge_outrights = Float(49, 56)
    short_option_minimum_charge_rate = Float(62, 69)
    adjustment_factor_members = Float(69, 72, scale=1e-2)
    adjustment_factor_hedgers = Float(72, 75, scale=1e-2)
    adjustment_factor_speculators = Float(75, 78, scale=1e-2)
    short_option_minimum_calculation_method = Int(78, 79)


@cython.cclass
class CommodityGroup(Base):
    """Commodity Group (Record Type: "5 ")

    >>> record("5 CME       06    07    14    31    3CC   71    76    7CC   AUW   BCF   ")
    CommodityGroup(code='CME', commodities=('06', '07', '14', '31', '3CC', '71', '76', '7CC', 'AUW', 'BCF'))
    """

    code = String(2, 5)
    commodities = Strings(12, 72, 6)


@cython.cclass
class FirstRiskArray(Base):
    """First Risk Array (Record Type: "81")

    >>> record("81CBT06        06        FUT 202507            000000000000+00000+00567-00567-00567+00567+01133-01133-01133+00000000284100N")
    FirstRiskArray(commodity='06', contract_day='', contract_month='202507', contract_type='FUT', exchange='CBT', option_day='', option_month='', option_right='', option_strike='0000000', risk=(0.0, 0.0, -0.0567, -0.0567, 0.0567, 0.0567, -0.11330000000000001, -0.11330000000000001, 0.11330000000000001), settlement_flag='N', settlement_price=2.841e-07, underlying_commodity='06')
    """

    exchange = String(2, 5)
    commodity = String(5, 15)
    underlying_commodity = String(15, 25)
    contract_type = String(25, 28)
    option_right = String(28, 29)
    contract_month = String(29, 35)
    contract_day = String(35, 37)
    option_month = String(38, 44)
    option_day = String(44, 46)
    option_strike = String(47, 54)
    risk = Risk(54, 108)
    settlement_price = Float(108, 122, scale=1e-12)
    settlement_flag = String(122, 123)


@cython.cclass
class SecondRiskArray(Base):
    """Second Risk Array (Record Type: "82")

    >>> record("82CBT06        06        OOFC202507   202507   000014500000+00000+00000+00000+00000+00000+00000+00000+002500000139100++10000+C")
    SecondRiskArray(commodity='06', composite_delta=0.0, contract_day='', contract_month='202507', contract_type='OOF', current_delta=10.0, current_delta_business_day='C', exchange='CBT', implied_volatility=0.25, option_day='', option_month='202507', option_right='C', option_strike='0000145', risk=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), settlement_price=0.1391, strike_sign='+', underlying_commodity='06')
    """

    exchange = String(2, 5)
    commodity = String(5, 15)
    underlying_commodity = String(15, 25)
    contract_type = String(25, 28)
    option_right = String(28, 29)
    contract_month = String(29, 35)
    contract_day = String(35, 37)
    option_month = String(38, 44)
    option_day = String(44, 46)
    option_strike = String(47, 54)
    risk = Risk(54, 96)
    composite_delta = Float(96, 101, scale=-1e-3)
    implied_volatility = Float(102, 110)
    settlement_price = Float(110, 117, scale=-1e-6)
    strike_sign = String(118, 119)
    current_delta = Float(119, 124, scale=-1e-3)
    current_delta_business_day = String(125, 126)


_RECORD_TYPES = {
    "0 ": ExchangeComplexHeader,
    "T ": CurrencyConversion,
    "1 ": ExchangeHeader,
    "2 ": FirstCombinedCommodity,
    "3 ": SecondCombinedCommodity,
    "4 ": ThirdCombinedCommodity,
    "5 ": CommodityGroup,
    "81": FirstRiskArray,
    "82": SecondRiskArray,
}


def record(s: str) -> Base:
    """Create PA2 record based on Record ID (first two characters)"""
    return _RECORD_TYPES[s[:2]](s)
