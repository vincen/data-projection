-- ----------------------------
-- Create role
-- Create database
-- grant privileges
-- ----------------------------
create user cc3 with password 'password';
create database cc3 owner cc3;
grant all privileges on database cc3 to cc3;


-- ----------------------------
-- Table structure for t_order
-- ----------------------------
DROP TABLE IF EXISTS "public"."t_order";
CREATE TABLE "public"."t_order" (
  "pkid" serial NOT NULL,
  "pid" varchar(255),
  "product_name" varchar(255),
  "price" numeric(8,2),
  "school" varchar(255),
  "count" int4,
  "updated_at" timestamp(6) with time zone NOT NULL DEFAULT now(),
  "order_time" date
);
ALTER TABLE "public"."t_order" OWNER TO "cc3";

-- ----------------------------
-- Primary Key structure for table t_order
-- ----------------------------
ALTER TABLE "public"."t_order" ADD CONSTRAINT "t_order_pkey" PRIMARY KEY ("pkid");


-- ----------------------------
-- Table structure for t_user
-- ----------------------------
DROP TABLE IF EXISTS "public"."t_user";
CREATE TABLE "public"."t_user" (
  "pkid" serial NOT NULL,
  "username" varchar(255),
  "nickname" varchar(255),
  "password" varchar(255),
  "created_at" timestamp(6) with time zone NOT NULL DEFAULT now()
);
ALTER TABLE "public"."t_user" OWNER TO "cc3";
-- ----------------------------
-- Primary Key structure for table t_user
-- ----------------------------
ALTER TABLE "public"."t_user" ADD CONSTRAINT "t_user_pkey" PRIMARY KEY ("pkid");


-- ----------------------------
-- Table structure for t_product
-- ----------------------------
DROP TABLE IF EXISTS "public"."t_product";
CREATE TABLE "public"."t_product" (
  "pkid" serial NOT NULL,
  "pid" varchar(255),
  "product_name" varchar(255),
  "school" varchar(255),
  "carrier" varchar(255),
  "is_boss" bool,
  "percentage" numeric(8,2)
);
ALTER TABLE "public"."t_product" OWNER TO "cc3";
-- ----------------------------
-- Primary Key structure for table t_product
-- ----------------------------
ALTER TABLE "public"."t_product" ADD CONSTRAINT "t_product_pkey" PRIMARY KEY ("pkid");


-- ----------------------------
-- Table structure for t_permission
-- ----------------------------
DROP TABLE IF EXISTS "public"."t_permission";
CREATE TABLE "public"."t_permission" (
  "pkid" serial NOT NULL,
  "user_id" int4,
  "school_code" varchar(255),
  "carrier" varchar(255)
);
ALTER TABLE "public"."t_permission" OWNER TO "cc3";
-- ----------------------------
-- Primary Key structure for table t_permission
-- ----------------------------
ALTER TABLE "public"."t_permission" ADD CONSTRAINT "t_permission_pkey" PRIMARY KEY ("pkid");


-- ----------------------------
-- View structure for v_order
-- ----------------------------
DROP VIEW IF EXISTS "public"."v_order";
CREATE VIEW "public"."v_order" AS
  SELECT
    o.order_time,
    o.school,
    r.carrier,
    CAST(SUM ( COUNT * CASE WHEN is_boss THEN r.percentage ELSE 1 END ) AS INT) AS orders 
  FROM
    t_order o,
    t_product r 
  WHERE
    o.pid = r.pid 
  GROUP BY
    o.order_time,
    o.school,
    r.carrier;


-- ----------------------------
-- View structure for v_order_2
-- ----------------------------
DROP VIEW IF EXISTS "public"."v_order_2";
CREATE VIEW "public"."v_order_2" AS
    SELECT
      tmp.order_time,
      tmp.school,
      tmp.carrier,
      COALESCE(SUM ( o."count" * CASE WHEN tmp.is_boss THEN tmp.percentage ELSE 1 END ), 0) :: INTEGER AS orders  
    FROM
      ( SELECT DAY :: DATE as order_time, t_product.* FROM generate_series ( '2019-02-15', now() - INTERVAL '1 d', INTERVAL '1 d' ) DAY, t_product ) tmp
    LEFT JOIN t_order o ON tmp.pid = o.pid AND tmp.order_time = o.order_time
    GROUP BY
      tmp.order_time,
      tmp.school,
      carrier 
    ORDER BY
      order_time DESC;


-- ----------------------------
-- View structure for v_order_3
-- ----------------------------
DROP VIEW IF EXISTS "public"."v_order_3";
CREATE VIEW "public"."v_order_3" AS
    SELECT
      tmp.order_time,
      tmp.school,
      tmp.carrier,
      COALESCE(SUM ( o."count" * CASE WHEN tmp.is_boss THEN tmp.percentage ELSE 1 END ), 0) :: INTEGER AS orders  
    FROM
      ( SELECT DAY :: DATE as order_time, t_product.* FROM generate_series ( '2019-02-15', now() - INTERVAL '1 d', INTERVAL '1 d' ) DAY, t_product ) tmp
    LEFT JOIN t_order o ON tmp.pid = o.pid AND o.order_time <= tmp.order_time
    GROUP BY
      tmp.order_time,
      tmp.school,
      carrier 
    ORDER BY
      order_time DESC;