"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from SymbolTable import SymbolTable
from VMWriter import VMWriter

class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """
    #def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
    def __init__(self, input_stream, output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        # Note that you can write to output_stream like so:
        # output_stream.write("Hello world! \n")
        self._token_file = input_stream
        self._symbol_table = SymbolTable()
        self._vm_writer = VMWriter(output_stream)
        self._while_count = 0
        self._if_count = 0
        self._exp_list_count = 0
        self._class_name = ""
        
    def compile_class(self) -> None:
        """Compiles a complete class."""
        #open
        self._token_file.advance() #""
        self._token_file.advance() #class
        self._class_name = self._token_file.identifier()
        self._token_file.advance() #class name
        self._token_file.advance() #{
        #create class symbol table
        while(True):
            if(self._token_file.token_type()=="KEYWORD"):
                if(self._token_file.keyword() not in {"STATIC", "FIELD"}):
                    break
                else:
                    self.compile_class_var_dec() #write one class var to symbol table
            else:
                break
        #compile subroutines
        while(True):
            if(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() == "}"):
                    break
            self.compile_subroutine() #write one func
        #end
        if(self._token_file.has_more_tokens()):
            self._token_file.advance() #}
        pass

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration.""" 
        #open
        kind = self._token_file.keyword() # static / field
        self._token_file.advance()
        # type / class name
        if(self._token_file.token_type == "KEYWORD"):
            type = self._token_file.keyword()
        else:
            type = self._token_file.identifier()    
        self._token_file.advance()
        #write var/s
        while(True):
            name = self._token_file.identifier() # var name
            self._token_file.advance()
            self._symbol_table.define(name, type, kind)
            #check if we are done
            if(self._token_file.token_type()=="SYMBOL"):
                if(self._token_file.symbol()==";"):
                    self._token_file.advance() # ;
                    break
                else:
                    self._token_file.advance() # ,
        #close
        pass

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        #open
        self._symbol_table.start_subroutine()
        #writre func
        if(self._token_file.keyword() == "CONSTRUCTOR"):
            self.write_constructor()
        else:
            self.write_func()
        self.write_subroutine_body()
        #close
        pass

    def write_constructor(self) -> None:
        func_locals = self.var_count()
        self._token_file.advance() # constructor
        self._vm_writer.write_function(self._class_name+".new", func_locals)
        self._token_file.advance()
        #alloc new object
        self._vm_writer.write_push("CONST", self._symbol_table.var_count("FIELD")) #object size
        self._vm_writer.write_call("Memory.alloc", 1)
        self._vm_writer.write_pop("pointer", 0) # this = object
        #cont
        self._token_file.advance() #new
        self._token_file.advance() #(
        self.compile_parameter_list() #check how much args and add them to the symbol table
        self._token_file.advance() #write )
        return
    
    def write_func(self) -> None:
        func_locals = self.var_count()
        func_or_method = self._token_file.keyword() #func / method
        self._token_file.advance()
        self._token_file.advance() #write type
        self._vm_writer.write_function(self._class_name+"."+self._token_file.identifier(), func_locals)
        self._token_file.advance()
        if(func_or_method == "METHOD"):
            self._vm_writer.write_push("argument", 0)
            self._vm_writer.write_pop("pointer", 0) #THIS = object
            self._symbol_table._arg_count = 1
        self._token_file.advance() # write (
        self.compile_parameter_list() #check how much args
        self._token_file.advance() # write )
        return

    def var_count(self) -> int:
        #TODO how much vars in the func
        line = self._token_file._line
        index = self._token_file._line_index
        token = self._token_file._token
        count = 0
        ret = 0
        #goes to the start of the func
        while(True):
            if(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() == "{"):
                    self._token_file.advance()
                    break
            self._token_file.advance()
        #run on the func
        while(count >= 0):
            if(self._token_file.token_type() == "KEYWORD"):
                #count all row
                if(self._token_file.keyword() == "VAR"):
                    ret +=1
                    self._token_file.advance() #var
                    self._token_file.advance() # type
                    self._token_file.advance() #varName
                    while(True):
                        if(self._token_file.token_type() == "SYMBOL"):
                            if(self._token_file.symbol() == ";"):
                                break
                            elif(self._token_file.symbol() == ","):
                                self._token_file.advance() # ,
                                ret += 1
                                self._token_file.advance() # var
            #check count
            elif(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() == "{"):
                    count += 1
                elif(self._token_file.symbol() == "}"):
                    count -= 1
            self._token_file.advance()
        self._token_file._line = line
        self._token_file._line_index = index
        self._token_file._token = token
        return ret

    def write_subroutine_body(self) -> None:
        self._token_file.advance() # {
        #VarDec + statements
        while(True):
            if(self._token_file.token_type() == "KEYWORD"):
                if(self._token_file.keyword() == "VAR"):
                    self.compile_var_dec() # add var to symbol table
                else:
                    break
            else:
                break
        self.compile_statements() 
        #close
        self._token_file.advance() # }
        pass

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        #check how much args and add them to the symbol table
        #no parameters
        if(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() == ")"):
                    return
        kind = "ARG" # arg
        # type / class name
        if(self._token_file.token_type == "KEYWORD"):
            type = self._token_file.keyword()
        else:
            type = self._token_file.identifier()    
        self._token_file.advance()
        name = self._token_file.identifier() # var_name
        self._token_file.advance()
        self._symbol_table.define(name, type, kind)
        while(True):
            if(self._token_file.symbol() == ")"):
                break
            self._token_file.advance() # ,
            # type / class name
            if(self._token_file.token_type == "KEYWORD"):
                type = self._token_file.keyword()
            else:
                type = self._token_file.identifier()   
            self._token_file.advance()
            name = self._token_file.identifier() # var_name
            self._token_file.advance()
            self._symbol_table.define(name, type, kind)
        return

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        kind = "VAR" #var
        self._token_file.advance()
        # type / class name
        if(self._token_file.token_type == "KEYWORD"):
            type = self._token_file.keyword()
        else:
            type = self._token_file.identifier()    
        self._token_file.advance()
        #write var/s
        while(True):
            name = self._token_file.identifier()
            self._token_file.advance()
            self._symbol_table.define(name, type, kind)
            #check if we are done
            if(self._token_file.token_type()=="SYMBOL"):
                if(self._token_file.symbol()==";"):
                    self._token_file.advance()
                    break
                else:
                    self._token_file.advance()
            else:
                return # error
        #close
        pass

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        #statments and var dec
        while(True):
            #end
            if(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() == "}"):
                    break
            if(self._token_file.token_type() == "KEYWORD"):
                if(self._token_file.keyword() == "RETURN"):
                    self.compile_return()
                    break
                elif(self._token_file.keyword() == "VAR"):
                    self.compile_var_dec()
                elif(self._token_file.keyword() == "DO"):
                    self.compile_do()
                elif(self._token_file.keyword() == "LET"):
                    self.compile_let()
                elif(self._token_file.keyword() == "IF"):
                    self.compile_if()
                elif(self._token_file.keyword() == "WHILE"):
                    self.compile_while()
            else:
                return #error
        #close
        pass

    def compile_do(self) -> None:
        """Compiles a do statement."""
        #open
        self._token_file.advance() # do
        call_name = self._token_file.identifier() # func name / class name
        self._token_file.advance()
        #body
        if(self._token_file.token_type() == "SYMBOL"):
            #func / method in the class
            if(self._token_file.symbol() == "("):
                self._vm_writer.write_push("pointer", 0)
                self._token_file.advance() # (
                self.compile_expression_list()
                self._token_file.advance() # )
                call_name = self._class_name + "." + call_name
                self._vm_writer.write_call(call_name, str(self._exp_list_count+1))
                self._exp_list_count = 0
                self._vm_writer.write_pop("temp", 0)
            #func / method in different class
            elif(self._token_file.symbol() == "."):
                #check if class_name is a object
                if(self._symbol_table.kind_of(call_name) in {"static", "field", "argument", "local"}):    
                    object_name = call_name
                    call_name = self._symbol_table.type_of(call_name)
                    call_name = call_name + self._token_file.symbol() # class_name.
                    self._token_file.advance()
                    call_name = call_name + self._token_file.symbol() # class_name.name
                    self._token_file.advance()
                    self._token_file.advance() # (
                    kind = self._symbol_table.kind_of(object_name)
                    if(kind == "field"):
                        kind = "this"
                    self._vm_writer.write_push(kind, self._symbol_table.index_of(object_name))
                    self.compile_expression_list()
                    self._token_file.advance() # )
                    self._vm_writer.write_call(call_name, str(self._exp_list_count+1))
                    self._exp_list_count = 0
                    self._vm_writer.write_pop("temp", 0)
                else:
                    call_name = call_name + self._token_file.symbol() # class_name.
                    self._token_file.advance()
                    call_name = call_name + self._token_file.symbol() # class_name.name
                    self._token_file.advance()
                    self._token_file.advance() # (
                    self.compile_expression_list()
                    self._token_file.advance() # )
                    self._vm_writer.write_call(call_name, str(self._exp_list_count))
                    self._exp_list_count = 0
                    self._vm_writer.write_pop("temp", 0)
            else:
                return #error
        self._token_file.advance() # ;
        pass

    def compile_let(self) -> None:
        """Compiles a let statement."""
        #open
        self._token_file.advance() # let
        var_name = self._token_file.identifier() #varName
        self._token_file.advance()
        #body
        if(self._token_file.token_type() == "SYMBOL"):
            #array
            if(self._token_file.symbol() == "["):
                array_memory_kind = self._symbol_table.kind_of(var_name)
                array_memory_index = self._symbol_table.index_of(var_name)
                self._vm_writer.write_push(array_memory_kind, array_memory_index)
                self._token_file.advance() # [
                self.compile_expression()
                self._token_file.advance() # ]
                self._vm_writer.write_arithmetic("ADD")
                self._token_file.advance() # =
                self.compile_expression()
                self._vm_writer.write_pop("temp", 0)
                self._vm_writer.write_pop("pointer", 1)
                self._vm_writer.write_push("temp", 0)
                self._vm_writer.write_pop("that", 0)
            else:
                self._token_file.advance() # =
                self.compile_expression()
                kind = self._symbol_table.kind_of(var_name)
                if(kind == "field"):
                    kind = "this"
                index = self._symbol_table.index_of(var_name)
                self._vm_writer.write_pop(kind, index)
        #not array
        else:
            self._token_file.advance() # =
            self.compile_expression()
            kind = self._symbol_table.kind_of(var_name)
            index = self._symbol_table.index_of(var_name)
            self._vm_writer.write_pop(kind, index)
        self._token_file.advance() # ;
        pass

    def compile_while(self) -> None:
        """Compiles a while statement."""
        #open
        self._vm_writer.write_label("while"+str(self._while_count)) # while
        temp = self._while_count
        self._while_count +=1
        self._token_file.advance()
        #body
        self._token_file.advance() # (
        self.compile_expression()
        self._token_file.advance() # )
        self._vm_writer.write_arithmetic("NOT") #change -1 to 0 and 0 to anything (-1)
        self._vm_writer.write_if("whileEnd"+str(temp))
        self._token_file.advance() # {
        self.compile_statements()
        self._vm_writer.write_goto("while"+str(temp))
        self._token_file.advance() # write }
        #close
        self._vm_writer.write_label("whileEnd"+str(temp)) # while end
        pass

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self._token_file.advance() # return
        if(self._token_file.token_type() == "SYMBOL"):
            #void func / method
            if(self._token_file.symbol() == ";"):
                self._vm_writer.write_push("constant", 0) #return null
                self._vm_writer.write_return()
                self._token_file.advance()
                return
            else:
                return #error
        elif(self._token_file.token_type() == "KEYWORD"):
            #constructor
            if(self._token_file.keyword() == "THIS"):
                self._vm_writer.write_push("pointer", 0) #retrun this
                self._vm_writer.write_return()
                self._token_file.advance()
                self._token_file.advance() # ;
                return
        else:
            self.compile_expression() #retrun expression
            self._vm_writer.write_return()
        self._token_file.advance() # ;
        pass

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        #open
        self._vm_writer.write_label("if"+str(self._if_count)) # if
        temp = self._if_count
        self._if_count +=1
        self._token_file.advance()
        #body
        self._token_file.advance() # (
        self.compile_expression()
        self._token_file.advance() # )
        self._vm_writer.write_arithmetic("NOT")
        self._vm_writer.write_if("else"+str(temp))
        self._token_file.advance() # {
        self.compile_statements()
        self._token_file.advance() # }
        self._vm_writer.write_goto("ifEnd"+str(temp))
        #write else even if there is no else
        self._vm_writer.write_label("else"+str(temp))
        if(self._token_file.token_type() == "KEYWORD"):
            if(self._token_file.keyword() == "ELSE"):
                self._token_file.advance() # else
                self._token_file.advance() # {
                self.compile_statements()
                self._token_file.advance() # }
        #close
        self._vm_writer.write_label("ifEnd"+str(temp))
        pass

    def compile_expression(self) -> None:
        """Compiles an expression."""
        #body
        self.compile_term()
        #more terms
        while(True):
            if(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() in {"+", "-", "*", "/", "&", "|", "<", ">", "="}):
                    if(self._token_file.symbol() == "="):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_arithmetic("EQ")
                    elif(self._token_file.symbol() == "+"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_arithmetic("ADD")         
                    elif(self._token_file.symbol() == "-"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_arithmetic("SUB")
                    elif(self._token_file.symbol() == "*"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_call("Math.multiply", 2)
                    elif(self._token_file.symbol() == "/"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_call("Math.divide", 2)
                    elif(self._token_file.symbol() == "&"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_arithmetic("AND")
                    elif(self._token_file.symbol() == "|"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_arithmetic("OR")
                    elif(self._token_file.symbol() == "<"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_arithmetic("LT")
                    elif(self._token_file.symbol() == ">"):
                        self._token_file.advance()
                        self.compile_term()
                        self._vm_writer.write_arithmetic("GT")
                else:
                    break
            else:
                break
        pass

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        #body
        temp = None
        if(self._token_file.token_type() == "SYMBOL"):
            #unaryOp
            if(self._token_file.symbol() in {"-", "~", "^", "#"}):
                temp = self._token_file.symbol()
                type = "symbol"
                self._token_file.advance()
            #expression list
            elif(self._token_file.symbol() == "("):
                self._token_file.advance() # write (
                self.compile_expression()
                self._token_file.advance() # write )
            else:
                return #error
        elif(self._token_file.token_type() == "IDENTIFIER"):
            temp = self._token_file.identifier()
            type = "identifier"
            self._token_file.advance()
        elif(self._token_file.token_type() == "INT_CONST"):
            temp = self._token_file.int_val()
            type = "integerConstant"
            self._token_file.advance()
        elif(self._token_file.token_type() == "STRING_CONST"):
            temp = self._token_file.string_val()
            type = "stringConstant"
            self._token_file.advance()
        elif(self._token_file.token_type() == "KEYWORD"):
            if(self._token_file.keyword() in {"TRUE", "FALSE", "NULL", "THIS"}):
                temp = self._token_file.keyword().lower()
                type = "keyword"
                self._token_file.advance()
            else:
                return #error
        #second half
        if(self._token_file.token_type() == "SYMBOL"):
            if(temp == None):
                return
            # array
            if(self._token_file.symbol() == "["):
                array_memory_kind = self._symbol_table.kind_of(temp)
                array_memory_index = self._symbol_table.index_of(temp)
                self._vm_writer.write_push(array_memory_kind, array_memory_index) #push array memory
                self._token_file.advance() # [
                self.compile_expression()
                self._token_file.advance() # ]
                self._vm_writer.write_arithmetic("ADD") #array index in the right spot
                self._vm_writer.write_pop("pointer", 1)
                self._vm_writer.write_push("that", 0)
            # call subroutine
            elif(self._token_file.symbol() == "("):
                # temp = func name
                if(temp in {"-", "~", "^", "#"}):
                    self.compile_term()
                    if(temp == "-"):
                        self._vm_writer.write_arithmetic("NEG")
                    elif(temp == "^"):
                        self._vm_writer.write_arithmetic("SHIFTLEFT")
                    elif(temp == "#"):
                        self._vm_writer.write_arithmetic("SHIFTRIGHT")
                    else:
                        self._vm_writer.write_arithmetic("NOT")
                else:
                    self._token_file.advance() # (
                    self.compile_expression_list()
                    self._token_file.advance() # )
                    temp = self._class_name + temp
                    self._vm_writer.write_call(temp, str(self._exp_list_count))
                    self._exp_list_count = 0
            elif(self._token_file.symbol() == "."):
                # temp = class name
                if(self._symbol_table.kind_of(temp) in {"static", "field", "argument", "local"}): #temp is object
                    object_name = temp
                    temp = self._symbol_table.type_of(temp)
                    kind = self._symbol_table.kind_of(object_name)
                    if(kind == "field"):
                        kind = "this"
                    temp = temp + self._token_file.symbol() # class_name.
                    self._token_file.advance()
                    temp = temp + self._token_file.symbol() # class_name.name
                    self._token_file.advance()
                    self._vm_writer.write_push(kind, self._symbol_table.index_of(object_name)) #push the object
                    self._token_file.advance() # (
                    self.compile_expression_list()
                    self._token_file.advance() # )
                    self._vm_writer.write_call(temp, str(self._exp_list_count+1))
                    self._exp_list_count = 0
                else:
                    temp = temp + self._token_file.symbol() # class_name.
                    self._token_file.advance()
                    temp = temp + self._token_file.symbol() # class_name.name
                    self._token_file.advance()
                    self._token_file.advance() # (
                    self.compile_expression_list()
                    self._token_file.advance() # )
                    self._vm_writer.write_call(temp,str(self._exp_list_count))
                    self._exp_list_count = 0
            else:
                if(type == "integerConstant"):
                    self._vm_writer.write_push("constant", temp)
                elif(type == "identifier"):
                    kind = self._symbol_table.kind_of(temp)
                    if(kind == "field"):
                        kind = "this"
                    index = self._symbol_table.index_of(temp)
                    self._vm_writer.write_push(kind, index)
                #"TRUE", "FALSE", "NULL", "THIS"
                elif(type == "keyword"):
                    if(temp == "true"):
                        self._vm_writer.write_push("constant", 1)
                        self._vm_writer.write_arithmetic("NEG")
                    elif(temp == "false"):
                        self._vm_writer.write_push("constant", 0)
                    elif(temp == "null"):
                        self._vm_writer.write_push("constant", 0)
                    else:
                        self._vm_writer.write_push("pointer", 0)
                elif(type == "stringConstant"):
                    #alloc the string
                    self._vm_writer.write_push("constant", len(temp)) #string len
                    self._vm_writer.write_call("String.new", 1) #call the constructor of String
                    self._vm_writer.write_pop("pointer", 1) #start of the string class object in that
                    #put the chars in memory
                    i=0
                    while(i<len(temp)):
                        self._vm_writer.write_push("pointer", 1) #push string start memory (arg 0)
                        self._vm_writer.write_push("constant", ord(temp[i])) #push char in ascii to add to memory (arg 2)
                        self._vm_writer.write_call("String.appendChar", 2) #string.method(int, char)
                        self._vm_writer.write_pop("pointer", 1) #push the string back to that
                        i+=1
                    #push the start of the String to the stack
                    self._vm_writer.write_push("pointer", 1)         
        elif(self._token_file.token_type() == "IDENTIFIER" or self._token_file.token_type() == "INT_CONST"):
            if(temp in {"-", "~", "^", "#"}):
                self.compile_term()
                if(temp == "-"):
                    self._vm_writer.write_arithmetic("NEG")
                elif(temp == "^"):
                    self._vm_writer.write_arithmetic("SHIFTLEFT")
                elif(temp == "#"):
                    self._vm_writer.write_arithmetic("SHIFTRIGHT")
                else:
                    self._vm_writer.write_arithmetic("NOT")
            else:
                if(type == "integerConstant"):
                    self._vm_writer.write_push("constant", temp)
                elif(type == "identifier"):
                    kind = self._symbol_table.kind_of(temp)
                    index = self._symbol_table.index_of(temp)
                    self._vm_writer.write_push(kind, index)
        else:
            if(type == "integerConstant"):
                self._vm_writer.write_push("constant", temp)
            elif(type == "identifier"):
                kind = self._symbol_table.kind_of(temp)
                if(kind == "field"):
                    kind = "this"
                index = self._symbol_table.index_of(temp)
                self._vm_writer.write_push(kind, index)
            elif(type == "stringConstant"):
                #alloc the string
                    self._vm_writer.write_push("constant", len(temp)) #string len
                    self._vm_writer.write_call("String.new", 1) #call the constructor of String
                    self._vm_writer.write_pop("pointer", 1) #start of the string class object in that
                    #put the chars in memory
                    i=0
                    while(i<len(temp)):
                        self._vm_writer.write_push("pointer", 1) #push string start memory (arg 0)
                        self._vm_writer.write_push("constant", ord(temp[i])) #push char in ascii to add to memory (arg 2)
                        self._vm_writer.write_call("String.appendChar", 2) #string.method(int, char)
                        self._vm_writer.write_pop("pointer", 1) #push the string back to that
                        i+=1
                    #push the start of the String to the stack
                    self._vm_writer.write_push("pointer", 1)
        pass

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        while(True):
            if(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() == ")"):
                    break
            self.compile_expression() #write to vm the expression
            self._exp_list_count +=1
            if(self._token_file.token_type() == "SYMBOL"):
                if(self._token_file.symbol() == ","):
                    self._token_file.advance() # ,
        pass