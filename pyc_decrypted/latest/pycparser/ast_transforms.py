#Embedded file name: pycparser/ast_transforms.py
from . import c_ast

def fix_switch_cases(switch_node):
    """ The 'case' statements in a 'switch' come out of parsing with one
        child node, so subsequent statements are just tucked to the parent
        Compound. Additionally, consecutive (fall-through) case statements
        come out messy. This is a peculiarity of the C grammar. The following:
    
            switch (myvar) {
                case 10:
                    k = 10;
                    p = k + 1;
                    return 10;
                case 20:
                case 30:
                    return 20;
                default:
                    break;
            }
    
        Creates this tree (pseudo-dump):
    
            Switch
                ID: myvar
                Compound:
                    Case 10:
                        k = 10
                    p = k + 1
                    return 10
                    Case 20:
                        Case 30:
                            return 20
                    Default:
                        break
    
        The goal of this transform it to fix this mess, turning it into the
        following:
    
            Switch
                ID: myvar
                Compound:
                    Case 10:
                        k = 10
                        p = k + 1
                        return 10
                    Case 20:
                    Case 30:
                        return 20
                    Default:
                        break
    
        A fixed AST node is returned. The argument may be modified.
    """
    assert isinstance(switch_node, c_ast.Switch)
    if not isinstance(switch_node.stmt, c_ast.Compound):
        return switch_node
    new_compound = c_ast.Compound([], switch_node.stmt.coord)
    last_case = None
    for child in switch_node.stmt.block_items:
        if isinstance(child, (c_ast.Case, c_ast.Default)):
            new_compound.block_items.append(child)
            _extract_nested_case(child, new_compound.block_items)
            last_case = new_compound.block_items[-1]
        elif last_case is None:
            new_compound.block_items.append(child)
        else:
            last_case.stmts.append(child)

    switch_node.stmt = new_compound
    return switch_node


def _extract_nested_case(case_node, stmts_list):
    """ Recursively extract consecutive Case statements that are made nested
        by the parser and add them to the stmts_list.
    """
    if isinstance(case_node.stmts[0], (c_ast.Case, c_ast.Default)):
        stmts_list.append(case_node.stmts.pop())
        _extract_nested_case(stmts_list[-1], stmts_list)
