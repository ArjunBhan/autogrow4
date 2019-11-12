##### mol_object_handling.py
import __future__

import rdkit
from rdkit import Chem

def check_sanitization(mol):
    """    
    Given a rdkit.Chem.rdchem.Mol this script will sanitize the molecule. 
    It will be done using a series of try/except statements so that if it fails it will return a None
    rather than causing the outer script to fail. 

    Nitrogen Fixing step occurs here to correct for a common RDKit valence error in which Nitrogens with
        with 4 bonds have the wrong formal charge by setting it to -1.
        This can be a place to add additional correcting features for any discovered common sanitation failures.
    
    Handled here so there are no problems later.
    
    Inputs: 
    :param rdkit.Chem.rdchem.Mol mol: an rdkit molecule to be sanitized
    Returns:
    :returns: rdkit.Chem.rdchem.Mol mol: A sanitized rdkit molecule or None if it failed.
    """
    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if mol is None:
        return None

    # If mol is wrong data type (excluding None) raise TypeError
    if type(mol) != rdkit.Chem.rdchem.Mol and type(mol) != rdkit.Chem.rdchem.RWMol:
        printout = "mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(mol))
        raise TypeError(printout)

    # easiest nearly everything should get through 
    try:
        sanitize_string =  Chem.SanitizeMol(mol, sanitizeOps = rdkit.Chem.rdmolops.SanitizeFlags.SANITIZE_ALL, catchErrors = True)
    except:
        return None
    
    if sanitize_string.name == "SANITIZE_NONE":    
        return mol
    else:
        # try to fix the nitrogen (common problem that 4 bonded Nitrogens improperly lose their + charges)
        mol = adjust_Nitrogen_charges(mol)
        Chem.SanitizeMol(mol, sanitizeOps = rdkit.Chem.rdmolops.SanitizeFlags.SANITIZE_ALL, catchErrors = True)
        sanitize_string =  Chem.SanitizeMol(mol, sanitizeOps = rdkit.Chem.rdmolops.SanitizeFlags.SANITIZE_ALL, catchErrors = True)
        if sanitize_string.name == "SANITIZE_NONE":    
            return mol

    # run a  sanitation Filter 1 more time incase something slipped through
    # ie. if there are any forms of sanition which fail ie. KEKULIZE then return None
    sanitize_string =  Chem.SanitizeMol(mol, sanitizeOps = rdkit.Chem.rdmolops.SanitizeFlags.SANITIZE_ALL, catchErrors = True)
    if sanitize_string.name != "SANITIZE_NONE":
        return None
    else:    
        return mol
#

def handle_hydrogens(mol, protanate_step):
    """
    Given a rdkit.Chem.rdchem.Mol this script will sanitize the molecule, remove all non-explicit H's
    and add back on all implicit H's. This is to control for any discrepencies in the smiles strings or presence and
    absense of H's. 
    If it fails it will return a None rather than causing the outer script to fail. Handled here so there are no problems later.
    
    Inputs: 
    :param rdkit.Chem.rdchem.Mol sanitized_deprotanated_mol: an rdkit molecule already sanitized and deprotanated.
    :param bol protanate_step: True if mol needs to be protanated; False if deprotanated
                                -Note if Protanated, smiles_merge takes up to 10times longer

    Returns:
    :returns: rdkit.Chem.rdchem.Mol mol: an rdkit molecule with H's handled (either added or removed) and sanitized.
                                            it returns None if H's can't be added or if sanitation fails   
    """

    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if mol is None:
        return None

    # If mol is wrong data type (excluding None) raise TypeError
    if type(mol) != rdkit.Chem.rdchem.Mol and type(mol) != rdkit.Chem.rdchem.RWMol:
        printout = "mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(mol))
        raise TypeError(printout)



    mol = check_sanitization(mol)
    if mol is None:
        # mol failed Sanitation
        return None
        
    mol = try_deprotanation(mol)
    if mol is None:
            # mol failed deprotanation
        return None

    if protanate_step is True:
        # PROTANTION IS ON
        mol = try_reprotanation(mol)
        if mol is None:
            # mol failed reprotanation
            return None

    return mol
#

def try_deprotanation(sanitized_mol):
    """
    Given an already sanitize rdkit.Chem.rdchem.Mol object, we will try to deprotanate the mol of all non-explicit
    Hs. If it fails it will return a None rather than causing the outer script to fail. 
       
    Inputs: 
    :param rdkit.Chem.rdchem.Mol mol: an rdkit molecule already sanitized.   
    Returns:
    :returns: rdkit.Chem.rdchem.Mol mol_sanitized: an rdkit molecule with H's removed and sanitized.
                                            it returns None if H's can't be added or if sanitation fails
    """    
    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if sanitized_mol is None:
        return None

    # If sanitized_mol is wrong data type (excluding None) raise TypeError
    if type(sanitized_mol) != rdkit.Chem.rdchem.Mol and type(sanitized_mol) != rdkit.Chem.rdchem.RWMol:
        printout = "sanitized_mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(sanitized_mol))
        raise TypeError(printout)
    
    try:
        mol = Chem.RemoveHs(sanitized_mol, sanitize=False)
    except:
        return None
    
    
    mol_sanitized = check_sanitization(mol)
    
    return mol_sanitized
#

def try_reprotanation(sanitized_deprotanated_mol):
    """
    Given an already sanitize and deprotanate rdkit.Chem.rdchem.Mol object, we will try to reprotanate the mol with
    implicit Hs. If it fails it will return a None rather than causing the outer script to fail. 
        
    Inputs: 
    :param rdkit.Chem.rdchem.Mol sanitized_deprotanated_mol: an rdkit molecule already sanitized and deprotanated.   
    Returns:
    :returns: rdkit.Chem.rdchem.Mol mol_sanitized: an rdkit molecule with H's added and sanitized.
                                            it returns None if H's can't be added or if sanitation fails
    """
    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if sanitized_deprotanated_mol is None:
        return None

    # If mol is wrong data type (excluding None) raise TypeError
    if type(sanitized_deprotanated_mol) != rdkit.Chem.rdchem.Mol and type(sanitized_deprotanated_mol) != rdkit.Chem.rdchem.RWMol:
        printout = "sanitized_deprotanated_mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(sanitized_deprotanated_mol))
        raise TypeError(printout)

    if sanitized_deprotanated_mol is not None:
        try:
            mol = Chem.AddHs(sanitized_deprotanated_mol)
        except:
            mol = None
        
        
        mol_sanitized = check_sanitization(mol)
        return mol_sanitized
    else:
        return None
#

def remove_atoms(mol, list_of_idx_to_remove):
    """
    This function removes atoms from an rdkit mol based on
    a provided list. The RemoveAtom function in Rdkit requires
    converting the mol to an more editable version of the rdkit mol
    object (Chem.EditableMol).

    Inputs:
    :param rdkit.Chem.rdchem.Mol mol: any rdkit mol
    :param list list_of_idx_to_remove: a list of idx values to remove
                                        from mol
    Returns:
    :returns: rdkit.Chem.rdchem.Mol new_mol: the rdkit mol as input but with
                                            the atoms from the list removed
    """
    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if mol is None:
        return None

    # If mol is wrong data type (excluding None) raise TypeError
    if type(mol) != rdkit.Chem.rdchem.Mol and type(mol) != rdkit.Chem.rdchem.RWMol:
        printout = "mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(mol))
        raise TypeError(printout)
    # If mol is wrong data type (excluding None) raise TypeError
    if type(list_of_idx_to_remove) != list:
        printout = "list_of_idx_to_remove is the wrong data type. \n"
        printout = printout + "Input should be a list\n"
        printout = printout + "Input list_of_idx_to_remove was {} type.".format(type(list_of_idx_to_remove))
        raise TypeError(printout)

    for i in list_of_idx_to_remove:
        if type(i) != int:
            printout = "list_of_idx_to_remove has the wrong data type within the list. \n"
            printout = printout + "It should be a list of interger\n"
            printout = printout + "But there is {} type within the list.".format(type(i))
            raise TypeError(printout)

    num_of_atoms_in_mol = len(mol.GetAtoms())
    # Check len of atoms is >= highest num in list
    for i in list_of_idx_to_remove:
        if i > num_of_atoms_in_mol-1:
            raise Exception("The highest index within list_of_idx_to_remove")
    
    try:        
        atomsToRemove = list_of_idx_to_remove
        atomsToRemove.sort(reverse = True)
    except:
        return None
        
    try:
        em1 = Chem.EditableMol(mol)
        for atom in atomsToRemove:
            em1.RemoveAtom(atom)
            
        new_mol = em1.GetMol()

        return new_mol
    except:
        return None
# 

def adjust_Nitrogen_charges(mol):
    """
    When importing ligands with sanitation turned off, one can successfully import
    import a SMILES in which a Nitrogen (N) can have 4 bonds, but no positive charge. 
    Any 4-bonded N lacking a positive charge will fail a sanitiation check.
        -This could be an issue with importing improper SMILES, reactions, or crossing a nuetral nitrogen
            with a side chain which adds an extra bond, but doesn't add the extra positive charge.

    To correct for this, this function will find all N atoms with a summed bond count of 4
    (ie. 4 single bonds;2 double bonds; a single and a triple bond; two single and a double bond)
    and set the formal charge of those N's to +1.

    RDkit treats aromatic bonds as a bond count of 1.5. But we will not try to correct for 
    Nitrogens labeled as Aromatic. As precaution, any N which is aromatic is skipped in this function.

    Inputs:
    :param rdkit.Chem.rdchem.Mol mol: any rdkit mol
    Returns:
    :returns: rdkit.Chem.rdchem.Mol mol: the same rdkit mol with the N's adjusted
    """
    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if mol is None:
        return None

    # If mol is wrong data type (excluding None) raise TypeError
    if type(mol) != rdkit.Chem.rdchem.Mol and type(mol) != rdkit.Chem.rdchem.RWMol:
        printout = "mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(mol))
        raise TypeError(printout)
    

    try:
        atoms = mol.GetAtoms()
    except:
        return None
        
    for atom in atoms:
        if atom.GetAtomicNum() == 7:
            bonds = atom.GetBonds()
            num_bond_sums = 0.0
            for bond in bonds:
                # GetBondTypeAsDouble prints out 1 for single, 2.0 for double, 
                # 3.0 for triple, 1.5 for AROMATIC
                num_bond_sums = num_bond_sums + bond.GetBondTypeAsDouble()
            # Check if the octet is filled
            if num_bond_sums == 4.0:
                atom.SetFormalCharge(+1)
    return mol
#

def check_for_unassigned_atom(mol):
    """
    Check there isn't a missing atom group ie. '*'
    A '*' in a SMILES string is an atom with an atomic num of 0
    """
    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if mol is None:
        return None

    # If mol is wrong data type (excluding None) raise TypeError
    if type(mol) != rdkit.Chem.rdchem.Mol and type(mol) != rdkit.Chem.rdchem.RWMol:
        printout = "mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(mol))
        raise TypeError(printout)
    
    try:
        atoms = mol.GetAtoms()
    except:
        return None

    for atom in atoms:
        if atom.GetAtomicNum()==0:
            return None
    return mol
#

def handle_frag_check(mol):
    """
    This will take a RDKit Mol object. It will check if it is fragmented.
    If it has fragments it will return the largest of the two fragments.
    If it has no fragments it will return the molecule on harmed. 
    """
    # None's often end up in a pipeline use of RDKit so we handle this data type as return None
    # instead of raise TypeError
    if mol is None:
        return None

    # If mol is wrong data type (excluding None) raise TypeError
    if type(mol) != rdkit.Chem.rdchem.Mol and type(mol) != rdkit.Chem.rdchem.RWMol:
        printout = "mol is the wrong data type. \n"
        printout = printout + "Input should be a rdkit.Chem.rdchem.Mol\n"
        printout = printout + "Input mol was {} type.".format(type(mol))
        raise TypeError(printout)
    
    try:
        frags = Chem.GetMolFrags(mol, asMols = True, sanitizeFrags = False)
    except:
        return None


    if len(frags)==1:
        return mol
    else:
        frag_info_list = []
        frag_index = 0
        for frag in frags:
            # Check for unassigned breaks ie. a '*' 
            frag = check_for_unassigned_atom(frag)
            if frag is None:
                frag_index = frag_index + 1
                continue
            else:
                num_atoms = frag.GetNumAtoms()
                frag_info = [frag_index, num_atoms]
                frag_info_list.append(frag_info)
                frag_index = frag_index + 1
        if len(frag_info_list) == 0:
            return None
        # Get the largest Fragment
        frag_info_list.sort(key = lambda x: float(x[-1]),reverse = True)
        largest_frag_idx = frag_info_list[0][0]
        largest_frag = frags[largest_frag_idx]
        return largest_frag
#