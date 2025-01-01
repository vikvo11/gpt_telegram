--затраты без кредита
select sum(cost),month from costs where month in(9,10,11,12) and title !='кредит'  group by month;

--затраты на кредит
select sum(cost),month from costs where month in(9,10,11,12) and title='кредит'  group by month;
-- затраты в сравнении
select title,cost,month from costs where month in(9,10,11,12) and title!='кредит' group by cost,month order by  title;
-- запросы по месецам
select title as test,(select cost from costs where month=12 and title =test) as '12',
(select cost from costs where month=11 and title =test) as '11',
(select cost from costs where month=10 and title =test) as '10',
(select cost from costs where month=9 and title =test) as '9',
(select cost from costs where month=8 and title =test) as '8',
(select cost from costs where month=7 and title =test) as '7' from costs  where month= 11;



#ALTER TABLE `costs` ADD `limit` INT( 11 ) NOT NULL;
#CREATE TABLE limit_dict (id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, title VARCHAR(20), limit_value INT);

#INSERT INTO limit_dict(title,limit_value) VALUES('продукты',25000);
#INSERT INTO limit_dict(title,limit_value) VALUES('детское',12000);
#INSERT INTO limit_dict(title,limit_value) VALUES('развлечение',7000);
#INSERT INTO limit_dict(title,limit_value) VALUES('няня',3500);
#INSERT INTO limit_dict(title,limit_value) VALUES('быт',2000);
#INSERT INTO limit_dict(title,limit_value) VALUES('обед',5000);
#INSERT INTO limit_dict(title,limit_value) VALUES('такси',1500);
#INSERT INTO limit_dict(title,limit_value) VALUES('одежда',4000);
#INSERT INTO limit_dict(title,limit_value) VALUES('общий',85000);

#INSERT INTO limit_dict(title,limit_value) VALUES('основной',85000);


select sum(cost),month from costs where month in(7,8,9,10,11) and year = 2020 and title !='кредит'  group by month;

select title,cost,(cost*3.43) as rub,month from costs where month in(11) and year = 2020;

select sum(cost),sum(cost*3.43) as rub,month from costs where month in(3,4,5,6,7,8,9,10,11) and year = 2020 and title !='квартира'  group by month;

----
select title,cost,month from costs where month in(3) and year=2021 and title!='кредит' group by cost,month order by  title;
select sum(cost),month from costs where month in(3) and year = 2021 and title !='кредит'  group by month;