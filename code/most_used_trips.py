import numpy as np
import pandas as pd
with pd.ExcelWriter("data/od_info.xlsx") as excelfile:
    for sheet_name in ["SZGK", "KK", "KP"]:
        od = pd.read_excel("data/bkk_adatok/OD.xlsx", sheet_name=sheet_name)
        zone_names_from = (od[od.columns[0]].astype('Int64').astype(str) + "_" + od[od.columns[1]].astype(str))[2:]
        zone_volumes_out = od.iloc[range(2,len(od)), 2]
        zone_names_to = [f"{od.iloc[range(len(od.columns)-1),0].astype('Int64')[ii]}_{od.iloc[ii,1]}"
                        for ii
                        in range(len(od.columns)-1)][2:]
        zone_volumes_in = od.iloc[1,range(3, len(od.columns))]
        od_matrix = od.iloc[range(2,len(od)), range(3,len(od.columns))].to_numpy()
        

        overall_movement = pd.merge(pd.DataFrame({"zone_name": zone_names_from,
                                                "volume_out": zone_volumes_out}),
                                    pd.DataFrame({"zone_name": zone_names_to,
                                                "volume_in": zone_volumes_in}),
                                    on = "zone_name",
                                    how = "inner")
        overall_movement.to_excel(excelfile,
                                  sheet_name=f"{sheet_name}_summary",
                                  index=False)
        pd.DataFrame(data=od_matrix, index=zone_names_from, columns=zone_names_to) \
            .to_excel(excelfile,
                      sheet_name=f"{sheet_name}_full_od")
        print(f"sheets: {", ".join(excelfile.sheets)}")


# Top 5 non-diag trip
sheet_name = "SZGK"
od = pd.read_excel("data/od_info.xlsx",
                   sheet_name=f"{sheet_name}_full_od",
                   header=0,
                   index_col=0)
od.drop(columns=[col for col in od.columns if not "Budapest" in col], inplace=True)
od.drop(index=[col for col in list(od.index) if not "Budapest" in col], inplace=True)
    

od_diag = pd.Series(od.to_numpy().diagonal(), index=od.index)

od_no_diag_arr = od.to_numpy(dtype=float, copy=True)
np.fill_diagonal(od_no_diag_arr, -np.inf)
od_no_diag = pd.DataFrame(od_no_diag_arr, index=od.index, columns=od.columns)

# 3. Stack the DataFrame and get the top 5 largest values
top_5 = (od_no_diag.stack()).nlargest(5)

# 4. Display the results
print("Top 5 values (excluding diagonal):")
for (row, col), val in top_5.items():
    print(f"Row: {row}, Column: {col} -> Value: {val}")

