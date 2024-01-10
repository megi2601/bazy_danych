drop table if exists "Studenci" CASCADE;
drop table if exists "Wybory" CASCADE;
drop table if exists "Wybory_Wyborcy" CASCADE;
drop table if exists "Wybory_Kandydaci" CASCADE;


CREATE TABLE "Studenci" (
	"nr_indeksu" TEXT NOT NULL,
	"haslo" char(5) NOT NULL DEFAULT 'haslo',
	"imie" TEXT NOT NULL,
	"nazwisko" TEXT NOT NULL,
	"czy_w_komisji" bool NOT NULL DEFAULT 'false',
	CONSTRAINT "Studenci_pk" PRIMARY KEY ("nr_indeksu")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "Wybory" (
	"nazwa" TEXT NOT NULL UNIQUE,
	"liczba_posad" integer NOT NULL,
	"termin_zglaszania" DATE NOT NULL,
	"termin_rozpoczecia" DATE NOT NULL,
	"termin_zakonczenia" DATE NOT NULL,
	"publikacja" bool NOT NULL DEFAULT 'false',
	CONSTRAINT "Wybory_pk" PRIMARY KEY ("nazwa")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "Wybory_Kandydaci" (
	"nazwa_wyborow" TEXT NOT NULL,
	"nr_indeksu_kandydata" TEXT NOT NULL,
	"liczba_glosow" integer DEFAULT 0,
	CONSTRAINT "Wybory_Kandydaci_pk" PRIMARY KEY ("nazwa_wyborow","nr_indeksu_kandydata")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "Wybory_Wyborcy" (
	"nazwa_wyborow" TEXT NOT NULL,
	"nr_indeksu_wyborcy" TEXT NOT NULL,
	"czy_zaglosowal" bool NOT NULL DEFAULT 'False',
	CONSTRAINT "Wybory_Wyborcy_pk" PRIMARY KEY ("nazwa_wyborow","nr_indeksu_wyborcy")
) WITH (
  OIDS=FALSE
);



ALTER TABLE "Wybory_Kandydaci" ADD CONSTRAINT "Wybory_Kandydaci_fk0" FOREIGN KEY ("nazwa_wyborow") REFERENCES "Wybory"("nazwa");
ALTER TABLE "Wybory_Kandydaci" ADD CONSTRAINT "Wybory_Kandydaci_fk1" FOREIGN KEY ("nr_indeksu_kandydata") REFERENCES "Studenci"("nr_indeksu");

ALTER TABLE "Wybory_Wyborcy" ADD CONSTRAINT "Wybory_Wyborcy_fk0" FOREIGN KEY ("nazwa_wyborow") REFERENCES "Wybory"("nazwa");
ALTER TABLE "Wybory_Wyborcy" ADD CONSTRAINT "Wybory_Wyborcy_fk1" FOREIGN KEY ("nr_indeksu_wyborcy") REFERENCES "Studenci"("nr_indeksu");

-- uzupełnij dane w Wybory_Wyborcy przy każdym dodaniu nowych wyborów

CREATE OR REPLACE FUNCTION dodaj_liste_wyborcow()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO "Wybory_Wyborcy" ("nazwa_wyborow", "nr_indeksu_wyborcy")
    SELECT NEW.nazwa, nr_indeksu FROM "Studenci" WHERE czy_w_komisji = FALSE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER wyborcy_trigger
AFTER INSERT ON "Wybory"
FOR EACH ROW
EXECUTE FUNCTION dodaj_liste_wyborcow();

-- uzupełnij dane o nowym wyborcy przy każdym dodaniu nowego studenta (tylko w wyborach które jeszcze się nie skończyły)

CREATE OR REPLACE FUNCTION uzupelnij_wyborce()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO "Wybory_Wyborcy" ("nazwa_wyborow", "nr_indeksu_wyborcy")
    SELECT nazwa, NEW.nr_indeksu
    FROM "Wybory"
    WHERE "Wybory".termin_zakonczenia < CURRENT_DATE 
	AND NEW.czy_w_komisji = FALSE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER uzupelnij
AFTER INSERT ON "Studenci"
FOR EACH ROW
EXECUTE FUNCTION uzupelnij_wyborce();

-- nie pozwól żeby członek komisji został kandydatem

CREATE OR REPLACE FUNCTION sprawdz_kandydata()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM "Studenci"
        WHERE nr_indeksu = NEW.nr_indeksu_kandydata AND czy_w_komisji = TRUE
    ) THEN
        RAISE EXCEPTION 'Kandydat nie moze byc w komisji.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER zakaz_komisja
BEFORE INSERT ON "Wybory_Kandydaci"
FOR EACH ROW
EXECUTE FUNCTION sprawdz_kandydata();


insert into "Studenci" (nr_indeksu, imie, nazwisko, czy_w_komisji) values ('ab000000','Anna', 'Bąk', 'false'), ('cd111111','Cela', 'Dom', 'true'),('ef222222','Elon', 'Fly', 'false'),('gh333333','Greta', 'Home', 'true'),('ij444444','Iza', 'Jan', 'false');
-- ('kl555555',5,k, l, True),
-- ('mn666666',6,m, n, False),
-- ('op777777',7,o, p, True),
-- ('qr888888',8,q, r, False),
-- ('st999999',9,s, t, True),
-- ('uv000000',1,u, v, False),
-- ('wx111111',1,w, x, True),
-- ('yz222222',1,y, z, False);

insert into "Wybory" values ('przewodniczacy', 1, '2023-12-10', '2023-12-12', '2023-12-14'); --zakonczone nieopublik
insert into "Wybory" values ('prezydent', 1, '2023-12-10', '2023-12-12', '2023-12-14', 'true'); --zakonczone opublik
insert into "Wybory" values ('samorzad', 4, '2024-01-2', '2024-01-10', '2024-02-20'); --glosowanie
insert into "Wybory" values ('rada', 1, '2024-03-2', '2024-03-12', '2024-03-14'); -- odbeda sie, zglos kandydata

insert into "Wybory_Kandydaci" values ('prezydent', 'ab000000', 3);
insert into "Wybory_Kandydaci" values ('prezydent', 'ef222222', 5);

insert into "Wybory_Kandydaci" values ('przewodniczacy', 'ab000000', 3);
insert into "Wybory_Kandydaci" values ('przewodniczacy', 'ij444444', 2);


insert into "Wybory_Kandydaci" values ('samorzad', 'ef222222');
insert into "Wybory_Kandydaci" values ('samorzad', 'ab000000');
insert into "Wybory_Kandydaci" values ('samorzad', 'ij444444');




