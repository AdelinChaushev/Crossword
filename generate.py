import copy

import sys
from queue import Queue
from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains.keys():
           for domain in copy.copy(self.domains[var]):
               if var.length != len(domain):
                   self.domains[var].remove(domain)
               


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        if self.crossword.overlaps[x,y]:
          xOverlap = self.crossword.overlaps[x,y][0]
          yOverlap = self.crossword.overlaps[x,y][1]

          xWords = copy.deepcopy(self.domains[x])
          for xWord in xWords:
           validOverlap = False
           for yWord in self.domains[y] :
               if xWord == yWord or xWord[xOverlap] == yWord[yOverlap]:
                   validOverlap = True
                   break
           if not validOverlap:
               self.domains[x].remove(xWord)
               revised = True

        return revised
               


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = list(self.crossword.overlaps.keys())
        q = Queue()
        for arc in arcs:
          q.put(arc)
        while not q.empty():
            item = q.get()
            if self.revise(item[0],item[1]):
                if len(self.domains[item[0]]) == 0:
                   return False;
                for neigbor  in self.crossword.neighbors(item[0]):
                    if neigbor != item[1]:
                        q.put((neigbor, item[0]))
        return True


            


    def assignment_complete(self, assignment):
        """
        crossword variable); return False otherwise.
        Return True if `assignment` is complete (i.e., assigns a value to each
        """
        for word in self.domains.keys():
            if word not in assignment.keys():
                return False
        return True    
             

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.

        """
        assigned = len(list(assignment.values()))
        distinct = len(set(assignment.values()))
        if assigned != distinct:
            return False

        for (x,y) in self.crossword.overlaps.keys():
          if self.crossword.overlaps[x,y] != None:
            if x in assignment.keys() and y in assignment.keys():

             if assignment[x][self.crossword.overlaps[x,y][0]] != assignment[y][self.crossword.overlaps[x,y][1]]:
                 return False



        for word in assignment.keys():
            if len(assignment[word]) != word.length:
                return False
        return True




    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        def removed(value):
          count  =0
          neighbors = self.crossword.neighbors(var)

          for neighbor in neighbors:
           if neighbor not in assignment.keys():
              vOverlap = self.crossword.overlaps[var,neighbor][0]
              nOverlap = self.crossword.overlaps[var, neighbor][1]
              if self.domains[neighbor] == value:
                  count+=1
              for word in  self.domains[neighbor]:
                if word[nOverlap] != value[vOverlap]:
                      count+= 1
           return count

        if self.domains[var] == None:
            return []
        ordered = sorted(self.domains[var], key=lambda  x: removed(x) )
        return ordered

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        vars = list(self.crossword.variables-set(assignment.keys()))
        sorted_vars_left = sorted(vars, key=lambda var: (len(self.domains[var]), -len(self.crossword.neighbors(var))))
        return sorted_vars_left[0] if sorted_vars_left else None

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if not self.consistent(assignment):
            return None
        if self.assignment_complete(assignment):
            return assignment
        variable = self.select_unassigned_variable(assignment)
        values = self.order_domain_values(variable, assignment)
        for domain in values:
            assignment[variable] = domain
            result = self.backtrack(assignment)
            if result == None:
                del assignment[variable]
            else:
              return result
        return None      


        
        



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
