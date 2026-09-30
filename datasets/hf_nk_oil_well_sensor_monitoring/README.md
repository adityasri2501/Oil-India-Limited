# Oil Well Sensor Monitoring Dataset: NK Field

Source: https://huggingface.co/datasets/Arailym-tleubayeva/NK-Oil-Well-Sensor-Monitoring

The source repository identifies the dataset license as Apache-2.0 and attributes industrial monitoring data to Galaz and Company LLP for a research project. This project downloaded `wells_dataset.csv` from the repository's `main` revision on 2026-09-30. The file is retained unchanged.

The source card reports 186,251 observations from 10 wells (7 sucker-rod pump wells), hourly samples from January through July 2026, and says the calendar year was assigned from monthly-file ordering because original timestamps did not include a year. It also reports outliers in the dynamometer-area channel. The PS120 benchmark excludes that channel and uses only range-filtered SRP readings for a separate sensor forecast. The publisher's source records and date assignment have not been independently verified.

SHA-256 of the downloaded CSV: `7A31FCA2A4709A3BF9513BDC5FE7ED8F66A543A8D4E0C6855282EE8DDE5F70B2`.

This is not Baghewala data. It does not include oil-production targets, CSS cycle records, or failure labels. It must not calibrate BGW-001 calculations or be used for operating decisions. Please retain this attribution and the dataset's license when redistributing the file.
