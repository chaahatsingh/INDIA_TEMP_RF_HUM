 1. Purpose: 
 Temperature Rainfall and humidity across various subdivisions in India to be able to correalate change in these conditions with how they affect sales of petrol and diesel.To be used eventually as a events table for the fuel forecating project
 2. Unit of observation:

One row per **IMD meteorological subdivision per calendar month**.

- `subdivision`: the region, using IMD's own subdivision names (for example,
  Konkan & Goa, Madhya Maharashtra, Marathwada, Vidarbha).
- `ds`: the first day of the month (for example, 2023-07-01), so that the
  table can later be joined on `ds` to monthly sales data without conversion.
- `region_type`: always `subdivision` in this version, so rows stay
  self-describing if other levels (states, districts) are added later.

A subdivision is used instead of a state because weather differs sharply
inside large states (for example, coastal Konkan vs. interior Maharashtra),
and subdivisions are IMD's own reporting unit for rainfall and temperature.
Subdivisions do not always follow state borders; where a subdivision spans
more than one state, no single state is assigned to it.

 3. Period:
January 2016 to the latest complete month available from all sources.
The end date will be confirmed once the IMD archive has been tested
(see Step 3) and recorded here. Every month in the period appears for
every subdivision; months where a value is unavailable are left blank
(NaN), never filled with 0.

4. Geography:

The 36 IMD meteorological subdivisions covering India, using IMD's
subdivision boundaries (to be confirmed once a boundary file is sourced).
Present-day boundaries are applied to the whole period, so that a
subdivision's values are comparable across all years. The aggregation
code takes a boundary file as an input, so the same pipeline can be run
at state or district level by supplying a different file.

5. Columns:
to be added
6. Missing data policy:
 Missing means blank (NaN), never 0. A zero rainfall month and an unknown month are different things
7. Sources:
8. Limitations: