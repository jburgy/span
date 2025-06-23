# Paris Expanded Format

## Introduction
SPAN risk parameter files are generated daily by Clearing Organizations which have implemented SPAN.

SPAN risk parameter files contain risk array records and other performance bond calculation parameter
records. These records contain all data values required to calculate SPAN risk and LIQUIDATION risk 
performance bond requirements, except individual firm or account portfolio data.

SPAN risk parameter files fall into two general classifications with regard to time: intra-day, and
settlement. 


## File format
This document describes the new Paris expanded unpacked fixed format, which are not supported by
PC-SPAN. All data is composed of printable text and records are no more than 132 bytes long.

Two concepts that were developed for use with SPAN are exchange complexes, and combined commodities.


## Exchange complexes
A SPAN risk parameter file contains SPAN risk parameter data for (a) a single "exchange complex" at
(b) a single point in time, typically the final end-of-day settlement.

A file for a single exchange complex, can contain data for any number of exchanges.


## Combined commodities
Combined commodities allow various products to be grouped together for the SPAN risk performance bond
calculation.

For any portfolio, SPAN will determine a risk requirement for each combined commodity represented in
the portfolio.

A combined commodity consists of all of the product families that are margined together in SPAN.


## Record types
Each record in a SPAN file begins with a record type code, also called the record ID.

Over the years since 1988 when SPAN was first developed, records with a numeric record types have been
considered to be primary record types and records with alphabetic record types have been considered to be
less-important sub-records. This distinction is less important today than previously. As general principles,
however:

- SPAN files may contain data that is less important in the sense that it is not required for the primary
purpose of the file, namely to allow SPAN performance bond calculations to be done. These data elements will
tend to be contained in sub-records, and may be ignored, if desired, by processes that need only to calculate
SPAN performance bond requirements.
- Programs that implement the SPAN algorithm should be constructed so that if they encounter a new record type,
or a known record type that is not needed, records of that type are simply skipped. This allows exchanges and
clearing organizations using SPAN to introduce new record types to meet changing business requirements, without
thereby necessitating immediate changes to such programs.

The various record types are:

| Type | Description                                                                  |
| ---- | -----------------------------------------------------------------------------|
| 0    | Exchange complex header                                                      |
| 1	   | Exchange header                                                              |
| 2    | First combined commodity definition record                                   |
| S    | Scanning Method Record                                                       |
| 3    | Second combined commodity definition record for Span Risk Calculation        |
| C    | Required Intra-commodity Spreads                                             |
| 33   | Second combined commodity definition record for Liquidation Risk Calculation |
| 4    | Third combined commodity definition record                                   |
| B    | Array Calculation Parameters                                                 |
| 5    | Combined commodity group record                                              |
| 6    | Inter-commodity spread record for Span Risk Calculation                      |
| 66   | Inter-commodity spread record for Liquidation Risk Calculation               |
| 8    | Risk array (contract) record                                                 |
| 9    | Price record for liquidation risk                                            |
| P    | Price Conversion Records (not used)                                          |
| T    | Currency Exchange Rate Records (not used)                                    |

See [this page](https://cmegroupclientsite.atlassian.net/wiki/spaces/pubsub/pages/457083445/Risk+Parameter+File+Layouts+for+the+Positional+Formats)

`span.pa2` relies on [python descriptors](https://docs.python.org/3/howto/descriptor.html) to strike a
balance between performance and memory footprint.
