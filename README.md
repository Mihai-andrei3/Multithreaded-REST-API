Nume: Ghita Mihai-Andrei
Grupă: 332CC

# Tema 1 Le Stats Sportif

## Organizare
***
### 1.Ce am invatat din aceasta tema:
* Am invatat cum sa fac un server API cu ajutorul Flask
* Am aprofunat cunostintele legate de programarea concurenta, implementand propriul ThreadPool si TaskRunner
* Am invatat cum sa mi fac propriile fisiere pentru testare

### 2.Explicatii solutie:
* ***task_runner***: 
  * In ***ThreadPool*** am implementat o coada pentru job-urile ce urmeaza sa fie rulate de catre threaduri, si o lista cu job-urile care sunt gata sau in curs de rulare.
De asemenea mai exista lista cu threaduri si evenimentul pentru graceful shtudown, iar la inchiderea sistemului se va trimite cate un task de tip-ul shutdown catre fiecare thread pentru a-i semnala oprirea.
  * In ***TaskRunner*** am implementat thread-ul care primeste referinta catre threadpool pentru a putea accesa coada de job-uri. Acesta ruleaza pana primeste shutdown si ia cate un job din coada, il executa si scrie rezultatul intr-un fisier. Nu exista busy waiting deoarece coada din python are mecanism default care evita acest lucru, si nu exista alte probleme de sincronizare.
* ***data Ingestor*** am preluat datele din csv intr-un dictionar, apoi le-am reorganizat in alt dictionar avand ca cheie statul si ca valoare intrarile pentru el, pentru a imi fi mai usor sa le
prelucrez. Acest ultim dictionar este referentiat si in Threadpool pentru accesarea datelor

* In ***TestWebServer***  am copiat codul scris pentru taskrunner si data ingestor. Am folosit un csv cu mai putine intrari, pentru a putea verifica care ar trebui sa fie rezultatul anumitor teste, si am implementat cate un test pentru fiecare metoda.

*  Consider ca implementarea mea putea fi mai eficienta, mai ales datorita modului de calul pentru media pe categorii, dar modul in care am implementat mi s-a parut mai usor de inteles.



****
### Implementare

* Toate cerintele temei au fost implementate
* Dificulatile principale au venit din cauze nefamiliaritatii cu biblioteca Flask si din cauza unittestelor 

***
### Resurse utilizate

* https://www.youtube.com/watch?v=zsYIw6RXjfM&t=450s&ab_channel=TechWithTim
* https://www.tutorialspoint.com/load-csv-data-into-list-and-dictionary-using-python
* https://www.youtube.com/watch?v=-ARI4Cz-awo&t=759s&ab_channel=CoreySchafer

