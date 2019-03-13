-- ----------------------------
-- Table structure for order_generalize
-- ----------------------------
DROP TABLE IF EXISTS "public"."order_generalize";
CREATE TABLE "public"."order_generalize" (
  "pkid" serial NOT NULL,
  "pid" varchar(255),
  "product_name" varchar(255),
  "price" numeric(8,2),
  "school" varchar(255),
  "count" int4,
  "updated_at" timestamp(6) without time zone NOT NULL DEFAULT now(),
  "order_time" date
);
ALTER TABLE "public"."order_generalize" OWNER TO "cc3";

-- ----------------------------
-- Primary Key structure for table order_generalize
-- ----------------------------
ALTER TABLE "public"."order_generalize" ADD CONSTRAINT "order_generalize_pkey" PRIMARY KEY ("pkid");


-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS "public"."user";
CREATE TABLE "public"."user" (
  "pkid" serial NOT NULL,
  "username" varchar(255),
  "nickname" varchar(255),
  "password" varchar(255),
  "created_at" timestamp(6) with time zone NOT NULL DEFAULT now()
);
ALTER TABLE "public"."user" OWNER TO "cc3";
-- ----------------------------
-- Primary Key structure for table user
-- ----------------------------
ALTER TABLE "public"."user" ADD CONSTRAINT "user_pkey" PRIMARY KEY ("pkid");


-- ----------------------------
-- Table structure for product
-- ----------------------------
DROP TABLE IF EXISTS "public"."product";
CREATE TABLE "public"."product" (
  "pkid" serial NOT NULL,
  "pid" varchar(255),
  "product_name" varchar(255),
  "school" varchar(255),
  "carrier" varchar(255),
  "is_boss" bool,
  "precentage" numeric(8,2)
);
ALTER TABLE "public"."product" OWNER TO "cc3";
-- ----------------------------
-- Primary Key structure for table product
-- ----------------------------
ALTER TABLE "public"."product" ADD CONSTRAINT "product_pkey" PRIMARY KEY ("pkid");

