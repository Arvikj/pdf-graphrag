# Chunk 1

Introduction
RocksDB is an embeddable persistent key-value store for fast storage environments. It uses a log-structured  database  engine,  written  entirely  in  C++  for  maximum performance. Over the years,  RocksDB  has  become  a  popular  choice  for  a  wide  range  of  applications,  including large-scale data processing, real-time analytics, and high-throughput transaction processing. It is  used  by  companies  such  as  Facebook  and  LinkedIn  to  power  their  critical  data-driven applications.  From  database  storage  engines such as MyRocks to application data caching to embedded  workloads,  RocksDB  can  be  used  for  a  variety  of  data  needs.  It  provides  basic operations  such  as  opening  and  closing  a  database,  reading  and  writing,  to  more advanced operations such as merging and compaction filters. For this assignment, we will be exploring the more basic functionalities of this Key-Value Store.
In  the  scope  of  this  assignment,  we  will  use subreddits.csv of  the Reddit database from the previous assignments. The subreddits.csv is also available here. Also, in this assignment, only high-level  steps  and  expectations  are mentioned. You are expected to explore the necessary requirements to solve the problem statement.

---

# Chunk 2

Step 0: Creating the setup for RocksDB (0 pts)
In  the  scope  of  this  assignment,  you MUST use  RocksDB  7.10.2.  Hence,  the  first  and  most important step is to familiarize yourself with RocksDB and create a working setup for RocksDB. No Docker containers will be provided for this assignment.
The  RocksDB  library  provides a persistent key-value store. Keys and values are arbitrary byte arrays. The keys are ordered within the key-value store according to a user-specified comparator function, rocksdb . You can refer here for some help on installation.
Note : If you are using M1/M2 setups, we advise you to work on a multi-architectural docker you can create on your own or provided in the previous assignments to avoid system-specific issues.

---

# Chunk 3

Step 1: Loading the Data (25 pts)
Template Here. RocksDB supports various write operations such as Put , Merge , and WriteBatch . These  operations  are  optimized  for  high performance, and have features such as memtable, write-ahead  log,  and  compaction  that  allow  for  efficient  and  persistent  write  operations, making RocksDB a popular choice for applications that require high write throughput and low latency.

---

