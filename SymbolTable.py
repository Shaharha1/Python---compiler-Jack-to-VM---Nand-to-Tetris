"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    CLASS_TYPE = {"STATIC", "FIELD"}
    SUBROUTINE_TYPE = {"ARG", "VAR"}
    TYPE_CELL = 0
    KIND_CELL = 1
    KIND_NUMBER = 2

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        #2 dict that have key:var_name and value:list of parameters
        self._class_dict = dict()
        self._subroutine_dict = dict()
        #counters for vars
        self._static_count = 0
        self._field_count = 0
        self._arg_count = 0
        self._var_count = 0
        pass

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        self._subroutine_dict.clear()
        self._arg_count = 0
        self._var_count = 0
        return

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        #will it delete it after the scope end?
        if(kind == "VAR"):
            temp = [type, "local", self.var_count(kind)]
        elif(kind == "ARG"):
            temp = [type, "argument", self.var_count(kind)]
        else:
            temp = [type, kind.lower(), self.var_count(kind)]
        if(kind in self.CLASS_TYPE):
            self._class_dict[name] = temp.copy()
            if(kind == "STATIC"):
                self._static_count +=1
            else:
                self._field_count +=1
        elif(kind in self.SUBROUTINE_TYPE):
            self._subroutine_dict[name] = temp.copy()
            if(kind == "ARG"):
                self._arg_count +=1
            else:
                self._var_count +=1
        return

    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        if(kind == "STATIC"):
            return self._static_count
        elif(kind == "FIELD"):
            return self._field_count
        elif(kind == "ARG"):
            return self._arg_count
        elif(kind == "VAR" or kind == "LOCAL"):
            return self._var_count
        return

    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        if(name in self._subroutine_dict):
            return self._subroutine_dict[name][self.KIND_CELL]
        if(name in self._class_dict):
             return self._class_dict[name][self.KIND_CELL]
        return

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        if(name in self._subroutine_dict):
            return self._subroutine_dict[name][self.TYPE_CELL]
        if(name in self._class_dict):
            return self._class_dict[name][self.TYPE_CELL]
        return

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        if(name in self._subroutine_dict):
            return self._subroutine_dict[name][self.KIND_NUMBER]
        if(name in self._class_dict):
            return self._class_dict[name][self.KIND_NUMBER]
        return
