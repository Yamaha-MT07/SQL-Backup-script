cd /d "C:\Program Files\MySQL\MySQL Server 8.0\bin"
set jour=%date:~0,2%
set mois=%date:~3,2%
set annee=%date:~6,4%
set madate=%annee%-%mois%-%jour%
mysqldump -u root -proot main_db >"C:\Users\Irek\Documents\Backup%madate%.sql"