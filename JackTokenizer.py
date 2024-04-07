"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    # Jack Language Grammar

    A Jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of whitespace characters, 
    and comments, which are ignored. There are three possible comment formats: 
    /* comment until closing */ , /** API comment until closing */ , and 
    // comment until the line's end.

    - 'xxx': quotes are used for tokens that appear verbatim ('terminals').
    - xxx: regular typeface is used for names of language constructs 
           ('non-terminals').
    - (): parentheses are used for grouping of language constructs.
    - x | y: indicates that either x or y can appear.
    - x?: indicates that x appears 0 or 1 times.
    - x*: indicates that x appears 0 or more times.

    ## Lexical Elements

    The Jack language includes five types of terminal elements (tokens).

    - keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
               'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' |
               'false' | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 
               'while' | 'return'
    - symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    - integerConstant: A decimal number in the range 0-32767.
    - StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
    - identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.

    ## Program Structure

    A Jack program is a collection of classes, each appearing in a separate 
    file. A compilation unit is a single class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    - class: 'class' className '{' classVarDec* subroutineDec* '}'
    - classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    - type: 'int' | 'char' | 'boolean' | className
    - subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
    - subroutineName '(' parameterList ')' subroutineBody
    - parameterList: ((type varName) (',' type varName)*)?
    - subroutineBody: '{' varDec* statements '}'
    - varDec: 'var' type varName (',' varName)* ';'
    - className: identifier
    - subroutineName: identifier
    - varName: identifier

    ## Statements

    - statements: statement*
    - statement: letStatement | ifStatement | whileStatement | doStatement | 
                 returnStatement
    - letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    - ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
                   statements '}')?
    - whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    - doStatement: 'do' subroutineCall ';'
    - returnStatement: 'return' expression? ';'

    ## Expressions
    
    - expression: term (op term)*
    - term: integerConstant | stringConstant | keywordConstant | varName | 
            varName '['expression']' | subroutineCall | '(' expression ')' | 
            unaryOp term
    - subroutineCall: subroutineName '(' expressionList ')' | (className | 
                      varName) '.' subroutineName '(' expressionList ')'
    - expressionList: (expression (',' expression)* )?
    - op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    - unaryOp: '-' | '~' | '^' | '#'
    - keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    Note that ^, # correspond to shiftleft and shiftright, respectively.
    """
    symbol_set = set(['{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>',
                          '=', '~', '^', '#'])

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.

        There are three possible comment formats: 
        /* comment until closing */ , /** API comment until closing */ , and 
        // comment until the line's end.
        """
        self._file = input_stream.read().splitlines()
        i=len(self._file)-1
        while(i>=0):
            #serach for cmd in line //
            has_cmd = self._file[i].find("//")
            if(has_cmd != -1):
                #delete cmd from line
                self._file[i] = self._file[i][:has_cmd]
            #delete API cmd
            has_cmd_end = self._file[i].find("*/") #end of cmd line
            if(has_cmd_end != -1): #has end cmd in line
                has_cmd = self._file[i].find("/**") #start of cmd line
                if(has_cmd != -1): #has start
                    self._file[i] = self._file[i][:has_cmd] + self._file[i][has_cmd_end+2:]
                else: #have more then 1 line in cmd
                    del self._file[i] #delete row
                    i -=1
                    while(True):
                        has_cmd = self._file[i].find("/**")
                        if(has_cmd != -1):
                            self._file[i] = self._file[i][:has_cmd]
                            break
                        del self._file[i] #delete row
                        i -=1
            #delete speace?
            self._file[i] = self._file[i].strip()
            #delete empty lines
            if(self._file[i] == ''):
                del self._file[i]
            i-=1
        #initialise token counter
        self._line = 0
        self._line_index = 0
        self._token = ""
        pass

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        if(self._line == len(self._file)): #cehck if we are in the last line
            return False
        return True

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        self._token = ""
        self._token = self._file[self._line][self._line_index]
        self.adv_index()
        #validate self._token
        while(True):
            if(self._token != " "):
                break
            self._token = self._file[self._line][self._line_index]
            self.adv_index()
        #check symbol type
        if(self._token in self.symbol_set): #symbol type
                return
        #check const_int
        if(self._token.isdigit()):
            while(self._token.isdigit()):
                if(not self._file[self._line][self._line_index].isdigit()):
                    return
                self._token = self._token + self._file[self._line][self._line_index]
                self.adv_index()
        #check string
        if(self._token == '"'):
            while(True):
                self._token = self._token + self._file[self._line][self._line_index]
                self.adv_index()
                if(self._token[len(self._token)-1]=='"'):
                    return
        #check words
        while(True):
            if(self._file[self._line][self._line_index] == " " or self._file[self._line][self._line_index] in self.symbol_set):
                return
            self._token = self._token + self._file[self._line][self._line_index]
            self.adv_index()

    def adv_index(self) -> None:
        #end of line
        if(self._line_index == len(self._file[self._line])-1):
            self._line_index = 0
            self._line +=1
        #next index in line
        else:
            self._line_index +=1

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        keyword_set = set(['class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int',
                            'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if',
                             'else', 'while', 'return'])
        if(self._token in keyword_set):
            return "KEYWORD"
        if(self._token in self.symbol_set):
            return "SYMBOL"
        if(self._token.isdigit()):
            return "INT_CONST"
        if(self._token[0]== '"'):
            return "STRING_CONST"
        return "IDENTIFIER"

    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        return self._token.upper()

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
            Recall that symbol was defined in the grammar like so:
            symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
        """
        return self._token

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
            Recall that identifiers were defined in the grammar like so:
            identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.
        """
        return self._token

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
            Recall that integerConstant was defined in the grammar like so:
            integerConstant: A decimal number in the range 0-32767.
        """
        return int(self._token)

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
            Recall that StringConstant was defined in the grammar like so:
            StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
        """
        return self._token[1:len(self._token)-1]

