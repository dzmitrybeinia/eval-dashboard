# Lesson name: Wprowadzenie do programowania w Pythonie: zmienne, typy danych i podstawowe operacje wejścia/wyjścia

## Intro

### Wprowadzenie do tematu

Python jest jednym z najpopularniejszych języków programowania na świecie dzięki swojej prostocie i wszechstronności. W tym temacie poznasz podstawowe elementy programowania w Pythonie, takie jak zmienne, typy danych oraz operacje wejścia i wyjścia. Te fundamenty pozwolą Ci tworzyć programy, które przechowują i manipulują danymi oraz komunikują się z użytkownikami.

#### **Themes:**
- Python jako język programowania

## Content slide

### Co to są zmienne?

Zmienne to podstawowe elementy każdego programu. Są to etykiety, które przechowują dane w pamięci komputera i mogą być modyfikowane w trakcie działania programu.

### Cechy zmiennych:
- Mają nazwy (np. `wiek`, `nazwa`, `cena`).
- Przechowują wartości danych (np. liczby, tekst).
- Mogą być modyfikowane w trakcie działania programu.

### Przykład:
```python
wiek = 15
print(wiek)  # Wyjście: 15
wiek = 16
print(wiek)  # Wyjście: 16
```

#### **Themes:**
- Definicja zmiennych
- Przykłady użycia zmiennych

## Content slide

### Typy danych w Pythonie

Typy danych określają rodzaj informacji, które zmienna może przechowywać. Python obsługuje różne typy danych, takie jak:

- **Integer (`int`)**: Liczby całkowite
  Przykład: `x = 10`
- **Float (`float`)**: Liczby dziesiętne
  Przykład: `cena = 19.99`
- **String (`str`)**: Tekst
  Przykład: `nazwa = "Ala"`
- **Boolean (`bool`)**: Wartości logiczne Prawda/Fałsz
  Przykład: `czy_student = True`

### Dlaczego typy danych są ważne?
Typy danych pomagają komputerowi zrozumieć, jak przechowywać i przetwarzać informacje.

### Przykład kodu:
```python
x = 5
y = 3.14
nazwa = "Jan"
czy_aktywny = False
print(x, y, nazwa, czy_aktywny)
```

#### **Themes:**
- Rodzaje typów danych
- Znaczenie typów danych

## Content slide

### Podstawowe operacje wejścia/wyjścia w Pythonie

Python umożliwia interakcję z użytkownikiem dzięki funkcjom wejścia i wyjścia.

### Wejście:
Funkcja `input()` pozwala użytkownikowi wprowadzić dane do programu.

Przykład:
```python
nazwa = input("Podaj swoje imię: ")
print("Cześć, " + nazwa + "!")
```

### Wyjście:
Funkcja `print()` wyświetla dane użytkownikowi.

Przykład:
```python
wiek = 15
print("Twój wiek to:", wiek)
```

### Łączenie wejścia i wyjścia:
Często używamy obu funkcji, aby stworzyć interaktywne programy.

Przykład:
```python
liczba = input("Podaj liczbę: ")
print("Podałeś liczbę:", liczba)
```

#### **Themes:**
- Funkcja input
- Funkcja print

## Content slide

### Łączenie elementów w programie

### Stwórzmy prosty program:
Poniżej znajduje się przykład programu, który wykorzystuje zmienne, typy danych oraz operacje wejścia/wyjścia:

```python
nazwa = input("Jak masz na imię? ")
wiek = int(input("Ile masz lat? "))
print("Cześć, " + nazwa + "! Masz " + str(wiek) + " lat.")

# Modyfikacja zmiennej
wiek_za_rok = wiek + 1
print("Za rok będziesz mieć " + str(wiek_za_rok) + " lat.")
```

### Wyjaśnienie:
- Program wykorzystuje `input()` do zbierania informacji od użytkownika.
- Zmienne przechowują imię i wiek użytkownika.
- Funkcja `int()` konwertuje wprowadzony tekst na liczbę całkowitą.
- Program oblicza wiek użytkownika za rok i wyświetla wynik za pomocą `print()`.

#### **Themes:**
- Tworzenie programu
- Interakcja z użytkownikiem

## Content slide

### Podsumowanie lekcji

### Kluczowe informacje:
- Zmienne to pojemniki na dane, których wartości mogą się zmieniać podczas działania programu.
- Python obsługuje różne typy danych, takie jak liczby całkowite, liczby dziesiętne, tekst i wartości logiczne.
- Funkcja `input()` pozwala użytkownikowi wprowadzać dane do programu, a `print()` wyświetla dane użytkownikowi.
- Łącząc zmienne, typy danych oraz operacje wejścia/wyjścia, możemy tworzyć interaktywne programy.

### Co dalej?
W następnej lekcji nauczymy się używać instrukcji warunkowych i pętli, aby tworzyć bardziej dynamiczne i elastyczne programy.

#### **Themes:**
- Podsumowanie kluczowych pojęć
- Zastosowanie w programowaniu
