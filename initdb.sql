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
  "updated_at" timestamp(6) without time zone NOT NULL DEFAULT now(),
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