#!/usr/bin/env python3
"""
PySpark script to count lines in Python files stored in GCS.
This script reads Python files from an input directory, counts lines in each file,
and writes the results to an output directory.
"""

import sys
from pyspark.sql import SparkSession

def main():
    if len(sys.argv) != 3:
        print("Usage: count_lines.py <input_path> <output_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Create Spark session
    spark = SparkSession.builder.appName("PythonLineCounter").getOrCreate()

    print(f"Reading Python files from: {input_path}")

    # Read all Python files
    try:
        # Read files as text
        files_rdd = spark.sparkContext.wholeTextFiles(input_path)

        # Count lines in each file
        # Format: (filename, line_count)
        line_counts = files_rdd.map(lambda x: (x[0].split('/')[-1], len(x[1].split('\n'))))

        # Collect results for display
        results = line_counts.collect()

        print("\n" + "="*60)
        print("HADOOP JOB OUTPUT - LINE COUNT RESULTS")
        print("="*60)

        total_lines = 0
        for filename, count in sorted(results):
            print(f"{filename}: {count} lines")
            total_lines += count

        print("="*60)
        print(f"Total files processed: {len(results)}")
        print(f"Total lines counted: {total_lines}")
        print("="*60 + "\n")

        # Save results to output path
        line_counts_with_header = line_counts.map(lambda x: f"{x[0]},{x[1]}")

        # Add header
        header_rdd = spark.sparkContext.parallelize(["filename,line_count"])
        output_rdd = header_rdd.union(line_counts_with_header)

        # Save to GCS
        output_rdd.coalesce(1).saveAsTextFile(output_path)

        print(f"Results saved to: {output_path}")

    except Exception as e:
        print(f"Error processing files: {str(e)}")
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
