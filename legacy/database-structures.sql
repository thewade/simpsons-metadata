-- Historical SQL structures from provided extract; NOT part of the static JSON API.
-- Some referenced tables have no definitions in the supplied extract.

CREATE TABLE `jokes` (
  `prodcode` varchar(7) NOT NULL,
  `jokes` text NOT NULL,
  `tags` text NOT NULL,
  `jokeorder` int NOT NULL DEFAULT '1',
  `indirect` int NOT NULL DEFAULT '0',
  `source` varchar(100) NOT NULL,
  `time` varchar(20) NOT NULL,
  KEY `prodcode` (`prodcode`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3;


-- Historical view: actorsjoin (requires other tables not included in SQL excerpt)
CREATE VIEW `actorsjoin` AS select `actors`.`actor` AS `actor`,`actors`.`fame` AS `fame`,`actors`.`character` AS `character`,`actors`.`pcode` AS `pcode`,`episodes`.`title` AS `title`,`episodes`.`airdate` AS `airdate`,`episodes`.`season` AS `season` from (`actors` join `episodes` on((`actors`.`pcode` = `episodes`.`prodcode`)));

-- Historical view: artworkjoin (requires other tables not included in SQL excerpt)
CREATE VIEW `artworkjoin` AS select `artwork`.`prodcode` AS `prodcode`,`artwork`.`filename` AS `filename`,`artwork`.`thumb` AS `thumb`,`artwork`.`alt` AS `alt`,`episodes`.`title` AS `title`,`episodes`.`airdate` AS `airdate`,`episodes`.`season` AS `season`,`artwork`.`order` AS `order` from (`episodes` join `artwork` on((`episodes`.`prodcode` = `artwork`.`prodcode`)));

-- Historical view: jokesjoin (requires other tables not included in SQL excerpt)
CREATE VIEW `jokesjoin` AS select `episodes`.`prodcode` AS `prodcode`,`episodes`.`tcode` AS `tcode`,`episodes`.`airdate` AS `airdate`,`episodes`.`title` AS `title`,`episodes`.`season` AS `season`,`jokes`.`jokes` AS `jokes`,`jokes`.`tags` AS `tags`,`episodes`.`Wikipedia` AS `Wikipedia`,`episodes`.`SNPP` AS `SNPP`,`jokes`.`indirect` AS `indirect`,`episodes`.`SHOWCODE` AS `showcode` from (`jokes` join `episodes` on((`jokes`.`prodcode` = `episodes`.`prodcode`)));
