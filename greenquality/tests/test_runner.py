"""
Кастомный тест-раннер с подробным выводом.
Подключается в settings.py: TEST_RUNNER = 'tests.test_runner.RussianDiscoverRunner'
"""
import sys
import unittest
from django.test.runner import DiscoverRunner


# Краткие описания тестов
ОПИСАНИЯ_ТЕСТОВ = {
    'test_airport_crud': 'CRUD для аэропорта (Airport)',
    'test_passenger_crud': 'CRUD для пассажира (Passenger)',
    'test_role_crud': 'CRUD для роли (Role)',
    'test_api_airports_list_and_create': 'API аэропортов: список, создание, чтение по id',
    'test_api_flights_list_search_upcoming': 'API рейсов: список, поиск, предстоящие',
    'test_export_statistics': 'Экспорт статистики (CSV/PDF) для менеджера',
}


class RussianTextTestResult(unittest.TextTestResult):
    """Результат тестов с выводом на русском и подробным логом."""

    def __init__(self, stream, descriptions, verbosity):
        # Всегда показывать каждый тест (как при verbosity=2)
        super().__init__(stream, descriptions, max(2, verbosity))
        self._test_index = 0
        self._total_tests = None

    def _description(self, test):
        """Краткое описание теста на русском."""
        desc = test.shortDescription()
        if desc:
            return desc.strip()
        method_name = getattr(test, '_testMethodName', '') or str(test)
        return ОПИСАНИЯ_ТЕСТОВ.get(method_name, method_name)

    def startTest(self, test):
        self._test_index += 1
        if self.showAll:
            desc = self._description(test)
            self.stream.write(f"  [{self._test_index}] {desc} ... ")
            self.stream.flush()
        super().startTest(test)

    def addSuccess(self, test):
        if self.showAll:
            self.stream.writeln("пройден")
            self.stream.flush()
        else:
            self.stream.write('.')
            self.stream.flush()
        # Вызываем TestResult напрямую, чтобы избежать дублирования "ok"
        unittest.TestResult.addSuccess(self, test)

    def addFailure(self, test, err):
        if self.showAll:
            self.stream.writeln("ПРОВАЛ")
            self.stream.flush()
        else:
            self.stream.write('F')
            self.stream.flush()
        super().addFailure(test, err)

    def addError(self, test, err):
        if self.showAll:
            self.stream.writeln("ОШИБКА")
            self.stream.flush()
        else:
            self.stream.write('E')
            self.stream.flush()
        super().addError(test, err)

    def addSkip(self, test, reason):
        if self.showAll:
            self.stream.writeln(f"пропущен ({reason})")
            self.stream.flush()
        super().addSkip(test, reason)

    def printErrors(self):
        """Вывод провалов и ошибок на русском."""
        if not self.failures and not self.errors:
            return
        self.stream.writeln()
        if self.failures:
            self.stream.writeln(self.separator1)
            self.stream.writeln("ПРОВАЛЫ ТЕСТОВ")
            self.stream.writeln(self.separator2)
            for test, err in self.failures:
                self.stream.writeln(f"  Тест: {self._description(test)}")
                self.stream.writeln(self.separator2)
                self.stream.writeln(err)
                self.stream.writeln()
        if self.errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("ОШИБКИ ВЫПОЛНЕНИЯ")
            self.stream.writeln(self.separator2)
            for test, err in self.errors:
                self.stream.writeln(f"  Тест: {self._description(test)}")
                self.stream.writeln(self.separator2)
                self.stream.writeln(err)
                self.stream.writeln()
        self.stream.flush()


class RussianTextTestRunner(unittest.TextTestRunner):
    """Запуск тестов с результатом на русском."""

    resultclass = RussianTextTestResult

    def __init__(self, verbosity=1, resultclass=None, **kwargs):
        # По умолчанию подробный вывод; resultclass от раннера Django
        super().__init__(
            verbosity=max(2, verbosity),
            resultclass=resultclass or RussianTextTestResult,
            **kwargs
        )

    def run(self, test):
        result = super().run(test)
        # Итоговая строка на русском
        self.stream.writeln('-' * 70)
        if result.wasSuccessful():
            self.stream.writeln(
                f"Выполнено тестов: {result.testsRun}, все пройдены успешно."
            )
        else:
            failed = len(result.failures) + len(result.errors)
            self.stream.writeln(
                f"Выполнено тестов: {result.testsRun}, "
                f"провалов/ошибок: {failed}."
            )
        self.stream.writeln()
        self.stream.flush()
        return result


class RussianDiscoverRunner(DiscoverRunner):
    """
    Django DiscoverRunner с подробным выводом на русском.
    Устанавливает verbosity=2 и свой класс результата.
    """

    test_runner = RussianTextTestRunner
    resultclass = RussianTextTestResult

    def __init__(self, verbosity=1, **kwargs):
        # Подробный вывод по умолчанию
        super().__init__(verbosity=max(2, verbosity), **kwargs)

    def run_suite(self, suite, **kwargs):
        """Запуск набора тестов с нашим runner и result class."""
        runner = self.test_runner(
            verbosity=self.verbosity,
            failfast=self.failfast,
            buffer=False,
            resultclass=self.resultclass,
        )
        return runner.run(suite)
