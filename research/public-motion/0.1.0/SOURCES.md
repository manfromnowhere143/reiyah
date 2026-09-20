# Public trajectory sources and limitations

Document ID: reiyah.public-motion.sources. Version 0.1.0.
Lifecycle status: exploratory. Accessed 20 September 2026.

Primary source: U.S. Department of Transportation Federal Highway Administration
(2016), *Next Generation Simulation (NGSIM) Vehicle Trajectories and Supporting
Data*, provided by ITS DataHub, [DOI 10.21949/1504477](https://doi.org/10.21949/1504477).
The retained [official catalog](https://catalog.data.gov/dataset/next-generation-simulation-ngsim-vehicle-trajectories-and-supporting-data),
[API metadata](https://data.transportation.gov/api/views/8ect-6jqj.json) and its
US-101 metadata PDF provide definitions and caveats. Exact capture hashes,
request URLs and metadata dates are in [sources.json](sources.json).

The PDF identifies its edition as version 1, published in 2016, and describes
US-101 collection on 15 June 2005. API table dates, metadata updates and HTTP
row-update headers differ; each is retained as a different field. This study
binds captured bytes and queries, not an invented immutable publisher release.

The sources define vehicle identifiers, millisecond timestamps, front-centre
longitudinal coordinates in feet, lengths and preceding identities. Identifiers
can repeat between recording contexts. The dataset reports tenth-second samples.
The selected location, bounded time envelope and duplicate checks constrain
identity use within this captured response; they do not establish global identity.

The PDF describes rough lateral/longitudinal accuracy of approximately two/four
feet, separately says attribute accuracy was not assessed, warns that records
can be missing, and prefers original TXT files to converted CSV. The Socrata
table's equivalence to original TXT files is not verified here. These limits
prevent a physical truth or continuous-motion interpretation of exact arithmetic
on the API decimals. No source media or original large archive is retrieved.

Current API licenseId and catalog point to CC BY-SA 3.0, while a current custom
metadata field points to CC BY-SA 4.0. The older PDF refers to RDE registration
and restricts redistribution. Preserve the inconsistency. The current public
API was accessed without authentication or bypass. No source body, reconstructed
trajectory, PDF or per-case numeric trace is redistributed. See
[DISTRIBUTION.md](DISTRIBUTION.md).

Web rendering could not open the metadata endpoint or PDF. Ordinary direct
public requests succeeded and their exact bodies were retained. A search result
named an older PDF asset; this study fetched the asset named by the current
official API metadata. Tool-rendering limitations are not evidence that the
source is absent.

A later physical experiment needs a calibrated position/dimension/clock error
contract, road-projected bumper geometry and a justified between-sample motion
family. More transformations of these same decimals cannot create those records.
