create database if not exists localchat;

create table if not exists chat (
	id serial not null,
	created_at timestamp default now(),
	primary key (id)
);

create table if not exists chat_messages (
	id serial not null,
	chat_id int,
	model text,
	role text,
	content text,
	created_at timestamp default now(),
	constraint fk_chat foreign key (chat_id) references chat(id),
	primary key (id)
);
