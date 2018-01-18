drop database tornado;

create database tornado charset=utf8;

use tornado;

create table tor_user_info(
		ui_user_id bigint unsigned auto_increment primary key comment '用户ID',
		ui_name varchar(32) not null comment '昵称',
		ui_passwd varchar(64) not null comment '密码',
		ui_mobile char(11) not null comment '手机号',
		ui_real_name VARCHAR(32) NULL comment '真实姓名',
		ui_id_card char(18) NULL comment '身份证号',
		ui_avatar varchar(128) null comment '头像',
		ui_admin tinyint NOT NULL DEFAULT '0' comment '是否是管理员， 0-不是，1-是',
		ui_ctime datetime default current_timestamp comment '创建时间',
		ui_utime datetime default current_timestamp on update current_timestamp comment '更新时间',
		UNIQUE (ui_name),
		unique (ui_mobile)
) engine=InnoDB auto_increment=10000 charset=utf8 comment '用户信息表';


CREATE TABLE tor_area_info(
    ai_area_id bigint unsigned NOT NULL PRIMARY KEY comment '区域id',
    ai_name VARCHAR(32) NOT NULL comment '区域名称',
    ai_ctime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP comment '创建时间'
) engine=InnoDB charset=utf8 comment '房源区域表';


create table tor_house_info(
    hi_house_id bigint unsigned auto_increment primary key comment '房屋ID',
    hi_user_id bigint unsigned not null comment '用户ID',
    hi_title varchar(64) not null comment '房屋名',
    hi_area_id bigint unsigned NOT NULL comment '房屋区域id',
    hi_address varchar(256) not null comment '房屋地址',
    hi_price int not null comment '房屋价格,单位分',
    hi_room_count tinyint unsigned NOT NULL DEFAULT '1' comment '房间数',
    hi_acreage int unsigned NOT NULL DEFAULT '0' comment '房屋面积',
    hi_house_unit VARCHAR(32) NOT NULL DEFAULT '' comment '房屋户型',
    hi_capacity int unsigned NOT NULL DEFAULT '1' comment '容纳人数',
    hi_beds VARCHAR(64) NOT NULL DEFAULT '' comment '床的配置',
    hi_deposit int unsigned NOT NULL DEFAULT '100000' comment '押金，单位分',
    hi_min_days int unsigned NOT NULL DEFAULT '1' comment '最短入住时间',
    hi_max_days int unsigned NOT NULL DEFAULT '0' comment '最长入住时间，0-不限制',
    hi_order_count int unsigned NOT NULL DEFAULT '0' comment '下单数量',
    hi_verify_status tinyint NOT NULL DEFAULT '0' comment '审核状态，0-待审核，1-审核为通过，2-审核通过',
    hi_online_status tinyint NOT NULL DEFAULT '1' comment '0-下架，1-上架',
    hi_index_image_url VARCHAR(256) NULL comment '房屋主图片',
    hi_ctime datetime not null default current_timestamp comment '创建时间',
    hi_utime datetime not null default current_timestamp on update current_timestamp comment '更新时间',
    KEY hi_status (hi_verify_status,hi_online_status),
    constraint foreign key (hi_user_id) references tor_user_info(ui_user_id)
) engine=InnoDB charset=utf8 comment '房屋信息表';


CREATE TABLE tor_house_facility(
    hf_id bigint unsigned NOT NULL PRIMARY KEY auto_increment comment '自增id',
    hf_house_id bigint unsigned NOT NULL comment '房屋id',
    hf_facility_id int unsigned NOT NULL comment '房屋设施',
    hf_ctime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP comment '创建时间',
    CONSTRAINT FOREIGN KEY (hf_house_id) REFERENCES tor_house_info(hi_house_id)
) engine=InnoDB charset=utf8 comment '房屋设施表';


CREATE TABLE tor_facility_catelog(
    fc_id int unsigned NOT NULL PRIMARY KEY auto_increment comment '自增id',
    fc_name VARCHAR(32) NOT NULL comment '设施名称',
    fc_ctime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP comment '创建时间'
) engine=InnoDB charset=utf8 comment '设施型录表';


CREATE TABLE tor_order_info (
    oi_order_id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '订单id',
    oi_user_id bigint unsigned NOT NULL COMMENT '用户id',
    oi_house_id bigint unsigned NOT NULL COMMENT '房屋id',
    oi_begin_date date NOT NULL COMMENT '入住时间',
    oi_end_date date NOT NULL COMMENT '离开时间',
    oi_days int unsigned NOT NULL COMMENT '入住天数',
    oi_house_price int unsigned NOT NULL COMMENT '房屋单价，单位分',
    oi_amount int unsigned NOT NULL COMMENT '订单金额，单位分',
    oi_status tinyint NOT NULL DEFAULT '0' COMMENT '订单状态，0-待接单，1-待支付，2-已支付，3-待评价，4-已完成，5-已取消，6-拒接单',
    oi_comment text NULL COMMENT '订单评论',
    oi_utime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    oi_ctime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (oi_order_id),
    KEY `oi_status` (oi_status),
    CONSTRAINT FOREIGN KEY (`oi_user_id`) REFERENCES `tor_user_info` (`ui_user_id`),
    CONSTRAINT FOREIGN KEY (`oi_house_id`) REFERENCES `tor_house_info` (`hi_house_id`)
) ENGINE=InnoDB CHARSET=utf8 COMMENT='订单表';


create table tor_house_image(
    hi_image_id bigint unsigned auto_increment primary key comment '房屋照片ID',
    hi_house_id bigint unsigned comment '房屋ID',
    hi_url varchar(128) not null comment '图片url',
    hi_ctime datetime not null default current_timestamp comment '创建时间',
    hi_utime datetime not null default current_timestamp on update current_timestamp comment '更新时间',
    constraint foreign key (hi_house_id) references tor_house_info(hi_house_id)
) engine=InnoDB charset=utf8 comment '房屋图片';