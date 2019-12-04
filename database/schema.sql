CREATE TABLE IF NOT EXISTS users(
	id int AUTO_INCREMENT,
	name varchar(50),
	email varchar(50),
	username varchar(50),
	password varchar(50)
);

CREATE TABLE IF NOT EXISTS messages(
	id int AUTO_INCREMENT,
	from_user varchar(50),
	to_user varchar(50),
	message_content varchar(350)
);

CREATE TABLE IF NOT EXISTS posts(
	id int AUTO_INCREMENT,
	posted_by varchar(50),
	post_content varchar(500)
);

