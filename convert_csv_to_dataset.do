import delimited using dataset.csv

rename v1 hr
rename v2 max_hr
rename v3 min_hr
rename v4 steps
rename v5 calories

gen mvpa = real(v8)
drop v8
