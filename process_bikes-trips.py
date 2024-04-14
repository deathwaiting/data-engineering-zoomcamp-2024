#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pyspark.sql import SparkSession
import pandas as pd
from pyspark.sql import types
from pyspark.sql.functions import year
from google.cloud import bigquery

# BigQuery client setup
client = bigquery.Client()
current_project_id = client.project

# Initialize a SparkSession
spark = SparkSession.builder\
                .config('spark.jars', 'gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.30.0.jar')\
                .getOrCreate()

# Read the CSV file into a DataFrame
schema = types.StructType([
    types.StructField("departure", types.TimestampType(), True),
    types.StructField("return", types.TimestampType(), True),
    types.StructField("departure_id", types.IntegerType(), True),
    types.StructField("departure_name", types.StringType(), True),
    types.StructField("return_id", types.IntegerType(), True),
    types.StructField("return_name", types.StringType(), True),
    types.StructField("distance (m)", types.DoubleType(), True),
    types.StructField("duration (sec.)", types.DoubleType(), True),
    types.StructField("avg_speed (km/h)", types.DoubleType(), True),
    types.StructField("departure_latitude", types.DoubleType(), True),
    types.StructField("departure_longitude", types.DoubleType(), True),
    types.StructField("return_latitude", types.DoubleType(), True),
    types.StructField("return_longitude", types.DoubleType(), True),
    types.StructField("Air temperature (degC)", types.DoubleType(), True)
    ])
    
raw = spark.read     .format("csv")     .option("compression", "gzip")     .option("header", True)     .option("inferSchema", True)    .schema(schema)    .load("gs://pfcllotsb7jsqqvbjrnw3s-datasets/bike-rides-data.tar.gz")


# In[2]:


# clean up column names, partition by year
raw = raw.withColumnRenamed("distance (m)", "distance")        .withColumnRenamed("duration (sec.)", "duration_sec")        .withColumnRenamed("avg_speed (km/h)", "avg_speed_km_h")        .withColumnRenamed("Air temperature (degC)", "air_temp_celcius")        .withColumn("year", year(raw["departure"]))

raw.printSchema()


# In[8]:


## get a table with all departure stations, removing duplicates
from pyspark.sql.functions import row_number, lit, col
from pyspark.sql.window import Window

window = Window.partitionBy("departure_longitude", "departure_latitude").orderBy(lit('A'))

departure_points = raw.filter(raw.departure_id.isNotNull())                    .select("departure_id", "departure_name", "departure_longitude", "departure_latitude")                    .distinct()                    .withColumn("row", row_number().over(window))                    .filter(col("row") == 1)                    .drop("row")

print(f"departure points num: {departure_points.count()}")
departure_points.show()

# save departure stations data into the datalake
table_path = f'gs://{current_project_id}-datalake/helinski-bike-trips/stations'
departure_points.write.mode("overwrite").parquet(table_path)


# In[9]:


#some years are missing departure id, so, we need to fill those using departure coordinates if possible
#Also some stations have multiple id's for the same name/coordinates, we should unify id's per coordinate
raw.createOrReplaceTempView('raw')
departure_points.createOrReplaceTempView('dept_points')

# cc = raw.filter(raw.departure_longitude.isNotNull()).count()
# print(f"raw rows with coordinates {cc}")

cleaned = spark.sql("""
                      SELECT raw.departure, raw.return, dept_points.departure_id as departure_id, raw.departure_name,raw.return_id, raw.return_name, 
                      raw.distance, raw.duration_sec, raw.avg_speed_km_h, raw.departure_latitude, 
                      raw.departure_longitude, raw.return_latitude, raw.return_longitude, 
                      raw.air_temp_celcius, raw.year
                      FROM raw
                      LEFT JOIN dept_points 
                      ON raw.departure_longitude = dept_points.departure_longitude AND raw.departure_latitude = dept_points.departure_latitude
                      """)\
                .filter(col("departure_id").isNotNull())

cleaned.printSchema()
print(f"raw data count: {raw.count()} / cleaned data count: {cleaned.count()}")


# In[10]:


# save clean data into datalake
root_path = f'gs://{current_project_id}-datalake/helinski-bike-trips'
cleaned.write.partitionBy("year").mode("overwrite").parquet(root_path)


# In[12]:


#############################################################################################
# Write the data to a bigQuery table, partitioned by year, clustered by departure_id
#############################################################################################
# Specify your dataset and table
dataset_id = 'zoomcamp_db'
table_id = 'helinski_bike_trips'
table_full_id = f"{client.project}.{dataset_id}.{table_id}"

# Write the DataFrame to BigQuery, schema should be inferred automatically from pyspark
cleaned.write.format("bigquery").option('table', table_full_id)     .option("writeMethod", "direct")     .option("partitionField", "departure")    .option("partitionType", "YEAR")    .option("clusteredFields", "departure_id")    .mode('overwrite')     .save()


# In[ ]:




