import argparse
import os
import glob
import json
import uuid
import pandas as pd

from massql import msql_extract


def _export_extraction(all_spectra, output_mzML_filename, output_mgf_filename, output_json_filename):
    # Returns two dataframes

    # Renumbering the scans when merging
    scan = 1
    for spectrum in all_spectra:
        spectrum["new_scan"] = scan
        scan += 1

    msql_extract._export_mzML(all_spectra, output_mzML_filename)
    msql_extract._export_mgf(all_spectra, output_mgf_filename)

    # Writing out JSON
    open(output_json_filename, "w").write(json.dumps(all_spectra))

    # Formatting output for tsv
    results_list = []

    for spectrum in all_spectra:
        for query_result in spectrum["query_results"]:
            query_result["new_scan"] = spectrum["new_scan"]
            query_result["new_filename"] = os.path.basename(output_mzML_filename)
            results_list.append(query_result)

    results_df = pd.DataFrame(results_list)

    return results_df

def main():
    parser = argparse.ArgumentParser(description="MSQL CMD")
    parser.add_argument('json_folder', help='json_folder')
    parser.add_argument('output_mzML_folder', help='Output mzML Folder')
    parser.add_argument('output_mgf_folder', help='Output mgf Folder')
    parser.add_argument('output_json_folder', help='Output merged JSON Folder')
    #parser.add_argument('output_parquet', help='Output Parquet File')
    parser.add_argument('output_tsv', help='Output Summary Extraction File')

    args = parser.parse_args()

    all_json_files = glob.glob(os.path.join(args.json_folder, "*.json"))

    print(all_json_files)

    file_number = 1
    MAX_SPECTRA_PER_EXTRACTION = 5000

    all_results_list = []
    all_spectra = []

    for json_filename in all_json_files:
        all_spectra += json.loads(open(json_filename).read())

        if len(all_spectra) > MAX_SPECTRA_PER_EXTRACTION:
            output_mzML_filename = os.path.join(args.output_mzML_folder, "extracted_{}.mzML".format(file_number))
            output_mgf_filename = os.path.join(args.output_mgf_folder, "extracted_{}.mgf".format(file_number))
            output_json_filename = os.path.join(args.output_json_folder, "extracted_{}.json".format(file_number))

            results_df = _export_extraction(all_spectra, output_mzML_filename, output_mgf_filename, output_json_filename)
            all_results_list.append(results_df)
            file_number += 1
            all_spectra = []

    if len(all_spectra) > 0:
        output_mzML_filename = os.path.join(args.output_mzML_folder, "extracted_{}.mzML".format(file_number))
        output_mgf_filename = os.path.join(args.output_mgf_folder, "extracted_{}.mgf".format(file_number))
        output_json_filename = os.path.join(args.output_json_folder, "extracted_{}.json".format(file_number))

        results_df = _export_extraction(all_spectra, output_mzML_filename, output_mgf_filename, output_json_filename)
        all_results_list.append(results_df)

    # Merging all the results
    merged_result_df = pd.concat(all_results_list)
    merged_result_df.to_csv(args.output_tsv, sep="\t", index=False)




    

    # Formatting the json peaks into a parquet data frame file
    # peak_list = []
    # for spectrum in all_spectra:
    #     sum_intensity = sum([peak[1] for peak in spectrum['peaks']])
    #     for peak in spectrum['peaks']:
    #         peak_dict = {}
    #         peak_dict["mz"] = peak[0]
    #         peak_dict["i"] = peak[1]
    #         peak_dict["i_norm"] = peak[1] / sum_intensity
            
    #         if "precursor_mz" in spectrum:
    #             peak_dict["precursor_mz"] = spectrum["precursor_mz"]

    #         # TODO: There could be multiple comments per spectrum
    #         try:
    #             if "comment" in spectrum["query_results"][0]:
    #                 peak_dict["comment"] = float(spectrum["query_results"][0]["comment"])
    #         except:
    #             pass

    #         peak_list.append(peak_dict)

    # peaks_df = pd.DataFrame(peak_list)
    # peaks_df.to_parquet(args.output_parquet)


if __name__ == "__main__":
    main()
