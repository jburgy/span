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
            s
            for index in range(self.start, self.stop, self.step)
            if (s := str(obj[index : index + self.step]).rstrip())
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
    scale: cython.double

    def __init__(
        self,
        start: cython.int,
        stop: cython.int,
        scale: cython.double = 1e-6,
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
    FirstCombinedCommodity(code='26', combination_margin_method='', commodity_1='26', commodity_2='26', commodity_3='59', commodity_4='WT1', commodity_5='VT1', commodity_6='GT1', contract_type_1='FUT', contract_type_2='OOF', contract_type_3='OOF', contract_type_4='OOF', contract_type_5='OOF', contract_type_6='OOF', exchange='CBT', limit_option_value='N', option_margin_style='P', performance_bond_currency_code='$', performance_bond_currency_iso='USD')
    """

    exchange = String(2, 5)
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
class RequiredSpreads(Base):
    """Required Spreads (Subrecord Type "C " of the type "3 " record)

    >>> record("C 06    1001030000100011401A021502B031601A")
    RequiredSpreads(charge_rate=9.999999999999999e-05, commodity='06', legs=('011401A', '021502B', '031601A'), number_of_legs=3, priority=1)
    """

    commodity = String(2, 8)
    priority = Int(10, 12)
    number_of_legs = Int(12, 14)
    charge_rate = Float(14, 21)
    legs = Strings(21, 77, 7)


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
class ArrayCalculationParameters(Base):
    """Array Calculation Parameters (Subrecord Type "B " of the type "4 " record)

    >>> record("B CBTZSC       OOC202507   202507   999999992500000000600030000330000000000000000000001000020250620ZSC       BC00000000Y0000035-0005000000000000 00 00 010000000000P 00")
    ArrayCalculationParameters(base_volatility=99.999999, base_volatility_exponent=0, commodity='ZSC', contract_day='', contract_month=202507, contract_type='OOC', coupon=0.0, delta_scaling_factor=1.0, discount_factor=1.0, equivalent_position_factor=nan, equivalent_position_factor_exponent=0, exchange='CBT', expiration_date=datetime.date(2025, 6, 20), expiration_price=-0.0035, expiration_price_flag='Y', extreme_move_covered_fraction=3.3000000000000003, extreme_move_multiplier=3.0, future_price_scan_range=0.6, interest_rate=0.0, lookahead_time=0.0, option_day='', option_month=202507, price_scan_range_exponent=0, price_scan_range_quotation='', pricing_model='BC', swap_value_factor=50000.0, swap_value_factor_exponent=0, time_to_expiration=0.0, underlying_commodity='ZSC', variable_tick='0', volatility_scan_range=2500000000.60003, volatility_scan_range_exponent=0, volatility_scan_range_quotation='P')
    """

    exchange = String(2, 5)
    commodity = String(5, 15)
    contract_type = String(15, 18)
    contract_month = Int(18, 24)
    contract_day = String(24, 26)
    option_month = Int(27, 33)
    option_day = String(33, 35)
    base_volatility = Float(36, 44)
    volatility_scan_range = Float(44, 62, scale=1e-8)
    future_price_scan_range = Float(52, 57, scale=1e-3)
    extreme_move_multiplier = Float(57, 62, scale=1e-3)
    extreme_move_covered_fraction = Float(62, 67, scale=1e-3)
    interest_rate = Float(67, 72, scale=1e-3)
    time_to_expiration = Float(72, 79)
    lookahead_time = Float(79, 85)
    delta_scaling_factor = Float(85, 91, scale=1e-4)
    expiration_date = Date(91)
    underlying_commodity = String(99, 109)
    pricing_model = String(109, 111)
    coupon = Float(111, 119)
    expiration_price_flag = String(119, 120)
    expiration_price = Float(120, 127, scale=-1e-4)
    swap_value_factor = Float(128, 142)
    swap_value_factor_exponent = Float(142, 144, scale=-1)
    base_volatility_exponent = Float(145, 147, scale=-1)
    volatility_scan_range_exponent = Float(148, 150, scale=-1)
    discount_factor = Float(151, 163, scale=1e-10)
    volatility_scan_range_quotation = String(163, 164)  # [A]bsolute or [P]ercentage
    price_scan_range_quotation = String(164, 165)  # [A]bsolute or [P]ercentage
    price_scan_range_exponent = Float(165, 167, scale=1)
    equivalent_position_factor = Float(143, 157)
    equivalent_position_factor_exponent = Int(157, 159)
    variable_tick = String(160, 161)


@cython.cclass
class PriceConversionParameters(Base):
    """Price Conversion Parameters (Subrecord Type "P " of the type "4 " record)

    >>> record("P CBT06        OOFSOYBEAN MEAL OP003000  000010000000000000000001USD$STD 00AMERSOYBEAN MEAL OPTIONS Long dated    YFEQTY DELIV                 0000001000000000  ")
    PriceConversionParameters(commodity='06', contract_type='OOF', contract_value_factor=10000000.0, contract_value_factor_exponent=0, exchange='CBT', exercise='AMER', futures_per_contract=1, long_name='SOYBEAN MEAL OPTIONS Long dated', money='F', positionable='Y', price_quotation='STD', settlement='DELIV', settlement_currency_code='$', settlement_currency_iso='USD', settlement_price_alignment='', settlement_price_decimal=3, short_name='SOYBEAN MEAL OP', standard_cabinet_option_value=0.0, strike_price_alignment='', strike_price_decimal=0, valuation='EQTY')
    """

    exchange = String(2, 5)
    commodity = String(5, 15)
    contract_type = String(15, 18)
    short_name = String(18, 33)
    settlement_price_decimal = Int(33, 36)
    strike_price_decimal = Int(36, 39)
    settlement_price_alignment = String(39, 40)
    strike_price_alignment = String(40, 41)
    contract_value_factor = Float(41, 55, scale=1e-2)
    standard_cabinet_option_value = Float(55, 63)
    futures_per_contract = Int(63, 65)
    settlement_currency_iso = String(65, 68)
    settlement_currency_code = String(68, 69)
    price_quotation = String(69, 72)
    contract_value_factor_exponent = Int(72, 75)
    exercise = String(75, 79)
    long_name = String(79, 114)
    positionable = String(114, 115)
    money = String(115, 116)  # [N]ominal, [I]nterest, [F]utures
    valuation = String(116, 121)
    settlement = String(121, 126)


@cython.cclass
class CommodityGroup(Base):
    """Commodity Group (Record Type: "5 ")

    >>> record("5 CME       06    07    14    31    3CC   71    76    7CC   AUW   BCF   ")
    CommodityGroup(code='CME', commodities=('06', '07', '14', '31', '3CC', '71', '76', '7CC', 'AUW', 'BCF'))
    """

    code = String(2, 5)
    commodities = Strings(12, 72, 6)


@cython.cclass
class InterCommoditySpread(Base):
    """Inter-Commodity Spread (Record Type: "6 ")

    >>> record("6 ALL00010980000NYMNNY-HH 0010000ANYMNNY-HP 0010000B                                    04NYMNNY-NG          S00100000001")
    InterCommoditySpread(commodity='ALL', credit_rate=0.98, group='S', leg1_commodity='NY-HH', leg1_exchange='NYM', leg1_ratio=1.0, leg1_required='N', leg1_side='A', leg2_commodity='NY-HP', leg2_exchange='NYM', leg2_ratio=1.0, leg2_required='N', leg2_side='B', leg3_commodity='', leg3_exchange='', leg3_ratio=nan, leg3_required='', leg3_side='', leg4_commodity='', leg4_exchange='', leg4_ratio=nan, leg4_required='', leg4_side='', method='04', minimum_legs=1, priority=1, target_commodity='NY-NG', target_delta=1.0, target_exchange='NYM', target_required='N')
    """

    commodity = String(2, 5)
    priority = Int(5, 9)
    credit_rate = Float(9, 16)
    leg1_exchange = String(16, 19)
    leg1_required = String(19, 20)
    leg1_commodity = String(20, 26)
    leg1_ratio = Float(26, 33, scale=1e-4)
    leg1_side = String(33, 34)
    leg2_exchange = String(34, 37)
    leg2_required = String(37, 38)
    leg2_commodity = String(38, 44)
    leg2_ratio = Float(44, 51, scale=1e-4)
    leg2_side = String(51, 52)
    leg3_exchange = String(52, 55)
    leg3_required = String(55, 56)
    leg3_commodity = String(56, 62)
    leg3_ratio = Float(62, 69, scale=1e-4)
    leg3_side = String(69, 70)
    leg4_exchange = String(70, 73)
    leg4_required = String(73, 74)
    leg4_commodity = String(74, 80)
    leg4_ratio = Float(80, 87, scale=1e-4)
    leg4_side = String(87, 88)
    method = String(88, 90)
    target_exchange = String(90, 93)
    target_required = String(93, 94)
    target_commodity = String(94, 100)
    group = String(109, 110)
    target_delta = Float(110, 117, scale=1e-4)
    minimum_legs = Int(117, 121)


@cython.cclass
class FirstRiskArray(Base):
    """First Risk Array (Record Type: "81")

    >>> record("81CBT06        06        FUT 202507            000000000000+00000+00567-00567-00567+00567+01133-01133-01133+00000000284100N")
    FirstRiskArray(commodity='06', contract_day='', contract_month=202507, contract_type='FUT', exchange='CBT', option_day='', option_month=None, option_right='', option_strike='0000000', risk=(0.0, 0.0, -0.0567, -0.0567, 0.0567, 0.0567, -0.11330000000000001, -0.11330000000000001, 0.11330000000000001), settlement_flag='N', settlement_price=2.841e-07, underlying_commodity='06')
    """

    exchange = String(2, 5)
    commodity = String(5, 15)
    underlying_commodity = String(15, 25)
    contract_type = String(25, 28)
    option_right = String(28, 29)
    contract_month = Int(29, 35)
    contract_day = String(35, 37)
    option_month = Int(38, 44)
    option_day = String(44, 46)
    option_strike = String(47, 54)
    risk = Risk(54, 108)
    settlement_price = Float(108, 122, scale=1e-12)
    settlement_flag = String(122, 123)


@cython.cclass
class SecondRiskArray(Base):
    """Second Risk Array (Record Type: "82")

    >>> record("82CBT06        06        OOFC202507   202507   000014500000+00000+00000+00000+00000+00000+00000+00000+002500000139100++10000+C")
    SecondRiskArray(commodity='06', composite_delta=0.0, contract_day='', contract_month=202507, contract_type='OOF', current_delta=10.0, current_delta_business_day='C', exchange='CBT', implied_volatility=0.25, option_day='', option_month=202507, option_right='C', option_strike='0000145', risk=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), settlement_price=0.1391, strike_sign='+', underlying_commodity='06')
    """

    exchange = String(2, 5)
    commodity = String(5, 15)
    underlying_commodity = String(15, 25)
    contract_type = String(25, 28)
    option_right = String(28, 29)
    contract_month = Int(29, 35)
    contract_day = String(35, 37)
    option_month = Int(38, 44)
    option_day = String(44, 46)
    option_strike = String(47, 54)
    risk = Risk(54, 96)
    composite_delta = Float(96, 101, scale=-1e-3)
    implied_volatility = Float(102, 110)
    settlement_price = Float(110, 117, scale=-1e-6)
    strike_sign = String(118, 119)
    current_delta = Float(119, 124, scale=-1e-3)
    current_delta_business_day = String(125, 126)


@cython.cclass
class ScanningMethod(Base):
    """Scanning Method (Record Type: "S ")

    >>> record("S 07    20020120250720250702202508202812                                          2")
    ScanningMethod(code=20, commodity='07', number_of_tiers=1, tier1_ending_month=202507, tier1_starting_month=202507, tier2_ending_month=202812, tier2_starting_month=202508, tier3_ending_month=None, tier3_starting_month=None, tier4_ending_month=None, tier4_starting_month=None, tier5_ending_month=None, tier5_starting_month=None, weighted_futures_method=2)
    """
    commodity = String(2, 8)
    code = Int(8, 10)
    number_of_tiers = Int(12, 14)
    tier1_starting_month = Int(14, 20)
    tier1_ending_month = Int(20, 26)
    tier2_starting_month = Int(28, 34)
    tier2_ending_month = Int(34, 40)
    tier3_starting_month = Int(42, 48)
    tier3_ending_month = Int(48, 54)
    tier4_starting_month = Int(56, 62)
    tier4_ending_month = Int(62, 68)
    tier5_starting_month = Int(70, 76)
    tier5_ending_month = Int(76, 82)
    weighted_futures_method = Int(82, 83)


@cython.cclass
class DailyAdjustmentsRates(Base):
    """Daily Adjustment Rates / Value Maintenance Rates (Record Type: "V ")
    
    >>> record("V CMEGA        202506  202506200000000000000+P0000000000000+P 100100Y100100Y100100GSCIER")
    DailyAdjustmentsRates(business_date=datetime.date(2025, 6, 20), commodity='GA', day='', exchange='CME', long_discount_or_premium='P', long_maintenance_rate=1.0, long_rate=0.0, month=202506, product_class='GSCIER', reset_long_down_threshold=1.0, reset_long_margin_flag='Y', reset_long_up_threshold=1.0, reset_short_down_threshold=1.0, reset_short_margin_flag='Y', reset_short_up_threshold=1.0, short_maintenance_rate=1.0, short_rate=0.0, short_rate_flag='')
    """
    exchange = String(2, 5)
    commodity = String(5, 15)
    month = Int(15, 21)
    day = String(21, 23)
    business_date = Date(23)
    long_rate = Float(31, 44, scale=-1e-6)
    long_discount_or_premium = String(45, 46)
    short_rate = Float(46, 59, scale=-1e-6)
    long_discount_or_premium = String(60, 61)
    short_rate_flag = String(61, 62)
    long_maintenance_rate = Float(62, 65, scale=1e-2)
    short_maintenance_rate = Float(65, 68, scale=1e-2)
    reset_long_margin_flag = String(68, 69)
    reset_long_down_threshold = Float(69, 72, scale=1e-2)
    reset_long_up_threshold = Float(72, 75, scale=1e-2)
    reset_short_margin_flag = String(75, 76)
    reset_short_down_threshold = Float(76, 79, scale=1e-2)
    reset_short_up_threshold = Float(79, 82, scale=1e-2)
    product_class = String(82, 88)


@cython.cclass
class CombinationMarginingMethod(Base):
    """Combination Margining Method (Record Type: "X ")

    >>> record("X M31        0000000")
    CombinationMarginingMethod(code='M', commodity='31', price_offset=0.0)
    """

    code = String(2, 3)  # [S]plit, [D]elta, [M]odified
    commodity = String(3, 13)
    price_offset = Float(13, 20)


@cython.cclass
class CombinationProductFamily(Base):
    """Option on Combination Product Family Definition (Record Type: "Y ")

    >>> record("Y 31        31 ")
    CombinationProductFamily(commodity='31', option='31')
    """

    commodity = String(2, 12)
    option = String(12, 22)


@cython.cclass
class CombinationUnderlyingLegs(Base):
    """Combination Underlying Legs (Record Type: "Z ")

    >>> record("Z CBT31        I/C  202507         001B010S         FUT202507  0000NL 0000000+")
    CombinationUnderlyingLegs(combination_type='I/C', commodity='31', day='', exchange='CBT', leg_commodity='S', leg_contract_day='', leg_contract_month=202507, leg_contract_type='FUT', leg_number=1, leg_price=0.0, leg_price_available='N', leg_price_usage='L', leg_ratio=0.0, leg_relationship='B', month=202507)
    """

    exchange = String(2, 5)
    commodity = String(5, 15)
    combination_type = String(15, 20)  # "STRIP", "CAL", or "I/C"
    month = Int(20, 26)
    day = String(26, 28)
    leg_number = Int(35, 38)
    leg_relationship = String(38, 39)
    leg_ratio = String(39, 42)
    leg_commodity = String(42, 52)
    leg_contract_type = String(52, 55)
    leg_contract_month = Int(55, 61)
    leg_contract_day = String(61, 63)
    leg_ratio = Float(63, 67, scale=1e-4)
    leg_price_available = String(67, 68)
    leg_price_usage = String(68, 70)
    leg_price = Float(70, 77, scale=-1e-6)


@cython.cclass
class SeriesIntracommoditySpreads(Base):
    """Series to Series Intracommodity Spreads (Record Type: "E ")
    
    >>> record("E 17    0000100002502509   010000A2512   020000B2603   010000A")
    SeriesIntracommoditySpreads(charge_rate=0.00025, commodity='17', leg1_market_side=nan, leg1_month=2509, leg1_ratio=0.01, leg1_remaining='', leg2_market_side=nan, leg2_month=2512, leg2_ratio=0.02, leg2_remaining='', leg3_market_side=nan, leg3_month=2603, leg3_ratio=0.01, leg3_remaining='', leg4_market_side=nan, leg4_month=None, leg4_ratio=nan, leg4_remaining='', priority=1)
    """
    commodity = String(2, 8)
    priority = Int(8, 13)
    charge_rate = Float(13, 20)
    leg1_month = Int(20, 24)
    leg1_remaining = String(24, 27)
    leg1_ratio = Float(27, 33)
    leg1_market_side = Float(33, 34)
    leg2_month = Int(34, 38)
    leg2_remaining = String(38, 41)
    leg2_ratio = Float(41, 47)
    leg2_market_side = Float(47, 48)
    leg3_month = Int(48, 52)
    leg3_remaining = String(53, 55)
    leg3_ratio = Float(55, 61)
    leg3_market_side = Float(61, 62)
    leg4_month = Int(62, 66)
    leg4_remaining = String(66, 69)
    leg4_ratio = Float(70, 75)
    leg4_market_side = Float(75, 76)


_RECORD_TYPES = {
    "0 ": ExchangeComplexHeader,
    "T ": CurrencyConversion,
    "1 ": ExchangeHeader,
    "2 ": FirstCombinedCommodity,
    "3 ": SecondCombinedCommodity,
    "C ": RequiredSpreads,
    "4 ": ThirdCombinedCommodity,
    "B ": ArrayCalculationParameters,
    "P ": PriceConversionParameters,
    "5 ": CommodityGroup,
    "6 ": InterCommoditySpread,
    "81": FirstRiskArray,
    "82": SecondRiskArray,
    "E ": SeriesIntracommoditySpreads,
    "S ": ScanningMethod,
    "V ": DailyAdjustmentsRates,
    "X ": CombinationMarginingMethod,
    "Y ": CombinationProductFamily,
    "Z ": CombinationUnderlyingLegs,
}


@cython.ccall
def record(s: str) -> Base:
    """Create PA2 record based on Record ID (first two characters)"""
    return _RECORD_TYPES[s[:2]](s)
