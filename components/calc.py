import math

# ----------------------------------------------------------------------------------------------------------------
# Calculator Component
# ----------------------------------------------------------------------------------------------------------------
# Simple class to make complicated calculations
# Used by the $calc command
# ----------------------------------------------------------------------------------------------------------------

class Calc():
    def __init__(self, bot):
        self.bot = bot
        self.expression = ""
        self.index = 0
        self.vars = {}
        self.funcs = ['cos', 'sin', 'tan', 'acos', 'asin', 'atan', 'cosh', 'sinh', 'tanh', 'acosh', 'asinh', 'atanh', 'exp', 'ceil', 'abs', 'factorial', 'floor', 'round', 'trunc', 'log', 'log2', 'log10', 'sqrt', 'rad', 'deg']

    def init(self):
        pass

    """reset()
    Reset the calculator state
    """
    def reset(self):
        self.index = 0
        self.vars = {
            'pi' : math.pi,
            'e' : math.e
        }
        self.funcs = ['cos', 'sin', 'tan', 'acos', 'asin', 'atan', 'cosh', 'sinh', 'tanh', 'acosh', 'asinh', 'atanh', 'exp', 'ceil', 'abs', 'factorial', 'floor', 'round', 'trunc', 'log', 'log2', 'log10', 'sqrt', 'rad', 'deg']

    """evaluate()
    Evaluate a mathematical expression and return the result
    
    Parameters
    ----------
    expression: Math expression
    vars: Variable
    
    Raises
    ------
    Exception: For any errors
    
    Returns
    --------
    float or int: Result
    """
    def evaluate(self, expression = "", vars={}):
        self.reset()
        self.expression = expression.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
        self.vars = {**self.vars, **vars}
        for func in self.funcs:
            if func in self.vars: raise Exception("Variable name '{}' can't be used".format(func))
        value = float(self.parse())
        if self.isNotDone(): raise Exception("Unexpected character '{}' found at index {}".format(self.peek(), self.index))
        epsilon = 0.0000000001
        if int(value) == value: return int(value)
        elif int(value + epsilon) != int(value):
            return int(value + epsilon)
        elif int(value - epsilon) != int(value):
            return int(value)
        return value

    """isNotDone()
    Return True if the evaluation isn't finished
    
    Returns
    --------
    bool: True if the evaluation isn't finished, False if it is
    """
    def isNotDone(self):
        return self.index < len(self.expression)

    """peek()
    Get the next element
    
    Returns
    --------
    str: Next element to be parsed
    """
    def peek(self):
        return self.expression[self.index:self.index + 1]

    """parse()
    Parse the next elements
    
    Returns
    --------
    float or int: Result
    """
    def parse(self):
        values = [self.multiply()]
        while True:
            c = self.peek()
            if c in ['+', '-']:
                self.index += 1
                if c == '-': values.append(- self.multiply())
                else: values.append(self.multiply())
            else:
                break
        return sum(values)

    """multiply()
    Multiply the next elements
    
    Returns
    --------
    float or int: Result
    """
    def multiply(self):
        values = [self.parenthesis()]
        while True:
            c = self.peek()
            match c:
                case '*' | 'x':
                    self.index += 1
                    values.append(self.parenthesis())
                case '/' | '%':
                    div_index = self.index
                    self.index += 1
                    denominator = self.parenthesis()
                    if denominator == 0:
                        raise Exception("Division by 0 occured at index {}".format(div_index))
                    if c == '/': values.append(1.0 / denominator)
                    else: values.append(1.0 % denominator)
                case '^':
                    self.index += 1
                    exponent = self.parenthesis()
                    values[-1] = values[-1] ** exponent
                case '!':
                    self.index += 1
                    values[-1] = math.factorial(values[-1])
                case _:
                    break
        value = 1.0
        for factor in values: value *= factor
        return value

    """parenthesis()
    Parse the elements in the parenthesis
    
    Raises
    ------
    Exception: Missing parenthesis
    
    Returns
    --------
    float or int: Result
    """
    def parenthesis(self):
        if self.peek() == '(':
            self.index += 1
            value = self.parse()
            if self.peek() != ')': raise Exception("No closing parenthesis found at character {}".format(self.index))
            self.index += 1
            return value
        else:
            return self.negative()

    """negative()
    Get the negative of the value
    
    Returns
    --------
    float or int: Result
    """
    def negative(self):
        if self.peek() == '-':
            self.index += 1
            return -1 * self.parenthesis()
        else:
            return self.value()

    """value()
    Get the value of the next element
    
    Returns
    --------
    float or int: Result
    """
    def value(self):
        if self.peek() in '0123456789.':
            return self.number()
        else:
            return self.variable_or_function()

    """variable_or_function()
    Get the result of a variable or a function
    
    Raises
    ------
    Exception: Error during the parsing
    
    Returns
    --------
    float or int: Result
    """
    def variable_or_function(self):
        var = ''
        while self.isNotDone():
            c = self.peek()
            if c.lower() in '_abcdefghijklmnopqrstuvwxyz0123456789':
                var += c
                self.index += 1
            else:
                break
        
        value = self.vars.get(var, None)
        if value == None:
            if var not in self.funcs: raise Exception("Unrecognized variable '{}'".format(var))
            else:
                param = self.parenthesis()
                match var:
                    case 'cos': value = math.cos(param)
                    case 'sin': value = math.sin(param)
                    case 'tan': value = math.tan(param)
                    case 'acos': value = math.acos(param)
                    case 'asin': value = math.asin(param)
                    case 'atan': value = math.atan(param)
                    case 'cosh': value = math.cosh(param)
                    case 'sinh': value = math.sinh(param)
                    case 'tanh': value = math.tanh(param)
                    case 'acosh': value = math.acosh(param)
                    case 'asinh': value = math.asinh(param)
                    case 'atanh': value = math.atanh(param)
                    case 'exp': value = math.exp(param)
                    case 'ceil': value = math.ceil(param)
                    case 'floor': value = math.floor(param)
                    case 'round': value = math.floor(param)
                    case 'factorial': value = math.factorial(param)
                    case 'abs': value = math.fabs(param)
                    case 'trunc': value = math.trunc(param)
                    case 'log':
                        if param <= 0: raise Exception("Can't evaluate the logarithm of '{}'".format(param))
                        value = math.log(param)
                    case 'log2':
                        if param <= 0: raise Exception("Can't evaluate the logarithm of '{}'".format(param))
                        value = math.log2(param)
                    case 'log10':
                        if param <= 0: raise Exception("Can't evaluate the logarithm of '{}'".format(param))
                        value = math.log10(param)
                    case 'sqrt': value = math.sqrt(param)
                    case 'rad': value = math.radians(param)
                    case 'deg': value = math.degrees(param)
                    case _: raise Exception("Unrecognized function '{}'".format(var))
        return float(value)

    """number()
    Return a numerical value
    
    Raises
    ------
    Exception: Error during the parsing
    
    Returns
    --------
    float or int: Result
    """
    def number(self):
        strValue = ''
        decimal_found = False
        c = ''
        
        while self.isNotDone():
            c = self.peek()
            if c == '.':
                if decimal_found:
                    raise Exception("Found an extra period in a number at character {}".format(self.index))
                decimal_found = True
                strValue += '.'
            elif c in '0123456789':
                strValue += c
            else:
                break
            self.index += 1
        
        if len(strValue) == 0:
            if c == '': raise Exception("Unexpected end found")
            else: raise Exception("A number was expected at character {}".format(self.index))
        return float(strValue)