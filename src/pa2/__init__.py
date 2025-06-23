"""Utilities to parse CME Span Risk Parameter Files."""

import datetime as dt

import cython


class String:
    def __init__(self, start: cython.int, stop: cython.int):
        self.start = start
        self.stop = stop

    def __get__(self, obj, objtype=None) -> str:
        return str(obj[self.start : self.stop]).rstrip()


class Float:
    def __init__(self, start: cython.int, stop: cython.int, scale: cython.float = 1e-6):
        self.start = start
        self.stop = stop
        self.scale = scale

    def __get__(self, obj, objtype=None) -> float:
        return int(obj[self.start : self.stop]) * self.scale


class Date:
    def __init__(self, start: cython.int):
        self.start = start

    def __get__(self, obj, objtype=None) -> dt.date:
        return dt.datetime.strptime(obj[self.start : self.start + 8], r"%Y%m%d").date()


class Time:
    def __init__(self, start: cython.int):
        self.start = start

    def __get__(self, obj, objtype=None) -> dt.time:
        try:
            return dt.datetime.strptime(
                obj[self.start : self.start + 4], r"%H%M"
            ).time()
        except ValueError:
            return dt.time()


class Spans:
    def __init__(self, start: cython.int, stop: cython.int):
        self.start = start
        self.stop = stop

    def __get__(self, obj, objtype=None) -> tuple[tuple[int, int], ...]:
        return tuple(
            (int(obj[index + 2 : index + 8]), int(obj[index + 8 : index + 14]))
            for index in range(self.start, self.stop, 14)
            if str(obj[index : index + 14]).isnumeric()
        )


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


class ExchangeComplexHeader(Base):
    """Exchange Complex Header (Record Type 0)

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


class ExchangeHeader(Base):
    """First Combined Commodity Record (Record Type 2)

    >>> record("1 CBT  01")
    ExchangeHeader(acronym='CBT', code='01')
    """

    acronym = String(2, 5)
    code = String(7, 9)


class FirstCombinedCommodity(Base):
    """First Combined Commodity Report (Subrecord Type: "2 ")

    >>> record("2 CBT 26    0USD$PN   26        FUT   26        OOF   59        OOF   WT1       OOF   VT1       OOF   GT1       OOF")
    FirstCombinedCommodity(code='26', combination_margin_method='', commodity_code_1='26', commodity_code_2='26', commodity_code_3='59', commodity_code_4='WT1', commodity_code_5='VT1', commodity_code_6='GT1', contract_type_1='FUT', contract_type_2='OOF', contract_type_3='OOF', contract_type_4='OOF', contract_type_5='OOF', contract_type_6='OOF', echange_acronym='CBT', limit_option_value='N', option_margin_style='P', performance_bond_currency_code='$', performance_bond_currency_iso='USD')
    """

    echange_acronym = String(2, 5)
    code = String(6, 12)
    performance_bond_currency_iso = String(13, 16)
    performance_bond_currency_code = String(16, 17)
    option_margin_style = String(17, 18)  # [P]remium or [F]uture
    limit_option_value = String(18, 19)  # [Y]es or [N]o
    combination_margin_method = String(19, 20)  # [S]plit, [D]elta, or [M]odified split
    commodity_code_1 = String(22, 32)
    contract_type_1 = String(32, 35)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_code_2 = String(38, 48)
    contract_type_2 = String(48, 51)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_code_3 = String(54, 64)
    contract_type_3 = String(64, 67)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_code_4 = String(70, 80)
    contract_type_4 = String(80, 83)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_code_5 = String(86, 96)
    contract_type_5 = String(96, 99)  # FUT, PHY, CMB, OOF, OOP, OOC
    commodity_code_6 = String(102, 112)
    contract_type_6 = String(112, 115)  # FUT, PHY, CMB, OOF, OOP, OOC


class SecondCombinedCommodity(Base):
    """Second Combined Commodity Record

    >>> record("3 06    1001202507202507022025082025080320250920250904202510202511  100010001100")
    SecondCombinedCommodity(code='06', init_to_maint_hedger=1.0, init_to_maint_member=1.0, init_to_maint_speculator=1.1, spread_charge_method='10', tiers=((202507, 202507), (202508, 202508), (202509, 202509), (202510, 202511)))
    """

    code = String(2, 8)
    spread_charge_method = String(8, 10)
    tiers = Spans(10, 66)
    init_to_maint_member = Float(68, 72, scale=1e-3)
    init_to_maint_hedger = Float(72, 76, scale=1e-3)
    init_to_maint_speculator = Float(76, 80, scale=1e-3)


_RECORD_TYPES = {
    "0 ": ExchangeComplexHeader,
    "T ": CurrencyConversion,
    "1 ": ExchangeHeader,
    "2 ": FirstCombinedCommodity,
    "3 ": SecondCombinedCommodity,
}


def record(s: str) -> Base:
    """Create PA2 record based on Record ID (first two characters)"""
    return _RECORD_TYPES[s[:2]](s)
