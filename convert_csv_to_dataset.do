import delimited using stata_data.csv

drop v1
drop v2

rename v3 hr
rename v4 max_hr
rename v5 min_hr
rename v6 steps
rename v7 calories

replace v8 = "1" if strpos(v8, "True")
replace v8 = "0" if strpos(v8, "False")

gen mvpa = real(v8)
drop v8
