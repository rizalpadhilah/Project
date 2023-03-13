# -*- coding: utf-8 -*-
"""PBL-38_Python.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BlkMZQn6tejKIchix8rMQ749FARx7-92

## **Demand Trend Analysis and Transaction Conversion Rate for Providing Better Customer Satisfaction**

Ralali.com merupakan salah satu business unit terbesar yang ada di ekosistem Ralali (Ralali.com, R-Connect, R-Agent) yang bergerak sebagai Marketplace Platform dimana platform ini menghubungkan antara user (buyer dan seller) untuk model bisnis B2B di Indonesia. 

Ralali ingin mengembangkan bisnisnya dengan menyesuaikan targeted market yang dituju dengan mengetahui pola dalam transactional data yang biasa dicapture dari tahun ke tahun. Untuk penyesuaian tersebut Ralali juga harus memperhatikan bagaimana kepuasan user dalam menggunakan platformnya sehingga perlu dilakukan monitoring terhadap transaksi, salah satunya dengan perhitungan conversion rate dari setiap proses yang dilalui user dalam bertransaksi.

Adapun dalam analisis kali ini berfokus pada peningkatan metrics Gross Merchandise Value (GMV)

### **Get the Data**
"""

#importing packages
import numpy as np
import pandas as pd
import seaborn as sns
import datetime as dt
from sklearn import linear_model
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from matplotlib import pyplot as plt
import os
from google.cloud import bigquery
from google.colab import drive
drive.mount('/content/drive')

#load private key JSON from google drive
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='/content/drive/MyDrive/Studi Independen - Bitlabs (Rizal)/private-key.json'

#get the data
bqclient = bigquery.Client()

# Download query results.
query_string = """
WITH tabel_gab AS (
SELECT
  *
FROM
  `G_CID_01.ralali_transactions_Q1_2018`
UNION ALL
SELECT
  *
FROM
  `G_CID_01.ralali_transactions_Q1_2019`
UNION ALL
SELECT
  *
FROM
  `G_CID_01.ralali_transactions_Q1_2020`
), 

tabel_gabungan AS (
  SELECT *,
  (price * product_quantity) AS gmv,
  (((price * product_quantity)) * (percentage_commission/100)) AS revenue,
  CASE
    WHEN payment_datetime IS NOT NULL THEN 'Paid'
  ELSE
  'Not Paid'
END
  AS is_paid,
  CASE
    WHEN payment_datetime IS NOT NULL AND received_datetime IS NULL THEN 'Refund'
  ELSE
  'Non Refund'
END
  AS refund_status
FROM
  tabel_gab
)

SELECT
  *
FROM
  tabel_gabungan
WHERE
  refund_status = 'Non Refund'
"""

df = (
    bqclient.query(query_string)
    .result()
    .to_dataframe(
        # Optionally, explicitly request to use the BigQuery Storage API. As of
        # google-cloud-bigquery version 1.26.0 and above, the BigQuery Storage
        # API is used by default.
    )
)

#display data
df.head()

"""### **Handling Missing Value**"""

#display info data
df.info()

#checking missing value each columns
df.isnull().any()

#handling missing value
df['processed_datetime'].fillna(df['payment_datetime'], inplace=True)
df['delivered_datetime'].fillna(df['payment_datetime'], inplace=True)
df['settled_datetime'].fillna(df['received_datetime'], inplace=True)
#convert datetime to year and month columns
df['Year'] = df['order_datetime'].dt.year
df['Month'] = df['order_datetime'].dt.month

#display info data
df.info()

"""## **Data Transformation**"""

#display categorical variable unique value
print(df['cat_name'].unique())
print(df['order_source'].unique())
print(df['logistic_name'].unique())
print(df['buyer_city_name'].unique())
print(df['payment_method'].unique())

#Replace string
df['order_source'] = df['order_source'].str.replace('Web Ralali', 'website')
df['payment_method'] = df['payment_method'].str.replace('BCA Bank Transfer', 'BCA')
df['payment_method'] = df['payment_method'].str.replace('Bank BCA', 'BCA')
df['payment_method'] = df['payment_method'].str.replace('BRI Bank Transfer', 'BRI')
df['payment_method'] = df['payment_method'].str.replace('Mandiri Bank Transfer', 'Mandiri')
df['payment_method'] = df['payment_method'].str.replace('Mandiri Internet Banking', 'Mandiri')
df['payment_method'] = df['payment_method'].str.replace('BNI Bank Transfer', 'BNI')

#check unique value
print(df['payment_method'].unique())

"""## **Data Description**"""

#check statistics descriptive and distribution data of gmv
print(df['gmv'].describe())
plt.figure(figsize=(10, 5))
sns.distplot(df['gmv'], color='b', bins=100, hist_kws={'alpha': 0.4});

#select variable numerical
df_num = df.select_dtypes(include = ['float64', 'int64'])
df_num.head()

#boxplot numerical variables
plt.figure(figsize=(18,9))
df_num.boxplot()
plt.title("Numerical variables in Ralali dataset", fontsize=20)
plt.show()

#countplot frequency order_source 
sns.countplot(data = df, x = 'order_source')

#countplot frequency category product
plt.figure(figsize=(10,5))
chart = sns.countplot(
    data=df,
    x='cat_name',
    palette='Set1'
)

plt.xticks(
    rotation=45, 
    horizontalalignment='right',
    fontweight='light',
    fontsize='x-large'  
)

#countplot frequency city
plt.figure(figsize=(25,5))
chart = sns.countplot(
    data=df,
    x='buyer_city_name',
    palette='Set1'
)

plt.xticks(
    rotation=90, 
    horizontalalignment='right',
    fontweight='light',
    fontsize='x-small'  
)

"""**Check Outlier**"""

# Q1, Q3, dan IQR
Q1 = df['gmv'].quantile(0.25)
Q3 = df['gmv'].quantile(0.75)
IQR = Q3 - Q1
print('Q1: ', Q1)
print('Q3: ', Q3)
print('IQR: ', IQR)
# Check ukuran sebelum data yang mengandung outliers dibuang
print('Shape awal: ', df.shape)
# Removing outliers
df_no_outliers = df[~((df['gmv'] < (Q1 - 1.5*IQR)) | (df['gmv'] > (Q3 + 1.5*IQR)))]
# Check ukuran  setelah data yang mengandung outliers dibuang
print('Shape akhir:', df_no_outliers.shape)

"""## **Exploratory Data Analysis**"""

#Top Highest GMV by City 
print('The TOP 5 City with Highest GMV 2018-2020')
total_gmv = df.groupby(by=['buyer_city_name'], as_index=False)['gmv'].sum()
total_gmv.sort_values(by='gmv', ascending=False).head()

#Annual GMV by City
by_city = pd.pivot_table(df, values='gmv', index=['buyer_city_name'], columns=['Year'],
                    aggfunc=np.sum)
by_city

#plot Annual GMV by City
by_city.plot(kind='bar', figsize=(50,7))
plt.xticks(rotation = 90)

"""**Insight**

Total GMV yang diterima Ralali mayoritas dihasilkan atau berasal dari Kota Besar. Wilayah di Jakarta menduduki peringkat teratas dalam akumulasi total GMV dari tahun 2018-2020

**Recommendations**

Perusahaan dapat memberikan promo berdasarkan segmentasi kota customers. Misalnya, pemberian promo ongkir atau promo harga untuk wilayah kota yang cukup jauh.
"""

#Top Highest GMV by Category Product
print('The TOP 5 Category Product with Highest GMV 2018-2020')
total_gmv = df.groupby(by=['cat_name'], as_index=False)['gmv'].sum()
total_gmv.sort_values(by='gmv', ascending=False).head()

#Annual GMV by Category Product
by_cat = pd.pivot_table(df, values='gmv', index=['cat_name'], columns=['Year'],
                    aggfunc=np.sum)
by_cat

#Plot Annual GMV by Category Product
by_cat.plot(kind='bar', figsize=(20,7))
plt.xticks(rotation = 45)

"""**Insight**

Kategori Product Automotive & Transportation menjadi product dengan akumulasi GMV tertinggi dari Q1 tahun 2018-2020.

**Recommendations**

Perusahaan dapat memberikan promo berdasarkan segmentasi kategori produk. Misalnya, perusahaan dapat memberi promo, diskon, atau menampilkan di menu utama untuk kategori yang masih sedikit peminatnya. Perusahaan juga bisa membuat pintasan atau product bundling untuk kategori product yang sering dibeli customers sehingga customers semakin mudah membeli productnya kembali.
"""

#GMV by Month
by_month = pd.pivot_table(df, values='gmv', index=['Month'], columns=['Year'],
                    aggfunc=np.sum)
by_month

#GMV by Month
by_month.plot(kind='bar', figsize=(20,7))
plt.xticks(rotation = 0)

"""**Insight**

Total GMV dari tahun ke tahun cenderung meningkat dengan nilai tertinggi berada pada bulan januari 2020.

**Recommendations**

Perusahaan dapat memberikan promo, reward, atau diskon untuk event tertentu yang ada pada setiap bulan.
"""

#GMV by Order Source
by_os = pd.pivot_table(df, values='gmv', index=['order_source'], columns=['Year'],
                    aggfunc=np.sum)
by_os

#GMV by OS
by_os.plot(kind='bar', figsize=(20,7))
plt.xticks(rotation = 0)

#checking correlation between numerical variables
corr = df_no_outliers.select_dtypes(include = ['float64', 'int64']).corr()
plt.figure(figsize=(10, 10))

sns.heatmap(corr[(corr >= 0.5) | (corr <= -0.4)], 
            cmap='viridis', vmax=1.0, vmin=-1.0, linewidths=0.1,
            annot=True, annot_kws={"size": 8}, square=True);

"""Insight

GMV berkorelasi positif kuat dengan revenue dan juga price.

Recommendations

Perusahaan dapat menaikkan sedikit harga barang untuk product yang sering dibeli customers sehingga dapat meningkatkan GMV.
"""

#filter data
df3 = df_no_outliers[['order_source', 'gmv']]
df3.head()

#Transform data to create dummy variable
df3["android"] = np.where(df3['order_source']=='Android', 1, 0) #D1 for Android
df3["website"] = np.where(df3['order_source']=='website', 1, 0) #D2 for Website
df3["ios"] = np.where(df3['order_source']=='ios', 1, 0) #D3 for ios
df3.head()

#define variable dependent and independent
x = df3[['android','website', 'ios']]
y = df3['gmv']

#build regression model
regr = linear_model.LinearRegression()
regr.fit(x, y)

print('Intercept: \n', regr.intercept_)
print('Coefficients: \n', regr.coef_)

# with statsmodels
x = sm.add_constant(x) # adding a constant
 
model = sm.OLS(y, x).fit()
predictions = model.predict(x) 
 
print_model = model.summary()
print(print_model)

"""Dengan mengambil taraf signifikansi 5%

Secara stimultan, jenis platform berperan terhadap GMV secara signifikan (p-value < 0.05). Diperoleh juga peran jenis platform terhadap GMV yaitu 7,8% ( R-Squared = 0.078) sedangkan sisanya dipengaruhi oleh variabel lain yang tidak dijelaskan dalam model.

Secara parsial, variabel dummy website berperan signifikan (p-value < 0.05). Pada variabel dummy website memiliki nilai GMV yang lebih tinggi dari platform yang lain. Sehingga ada perbedaan dari jenis platform terhadap nilai GMV.

## **Conclusion**
Terdapat pengaruh dari jenis platform yang digunakan customers terhadap nilai GMV. Adapun langkah yang perlu dilakukan agar meningkatkan GMV dari berbagai platform sebagai berikut.

1. Melakukan pengoptimalan kualitas semua platform ralali agar customers mendapatkan experience yang sama dalam setiap platform yang digunakan.

2. Memberi perlakuan yang berbeda kepada customers untuk setiap platform. Misalkan memberi promo untuk setiap instalasi aplikasi Ralali di Android atau ios sehingga branding dari ralali bisa ikut meningkat.

3. Memberikan pelayanan terbaik seperti pemberian diskon, pengiriman gratis, dan sebagainya
"""