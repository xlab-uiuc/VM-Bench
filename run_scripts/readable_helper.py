import re
import subprocess
import os

def split_line_remove_number(line):
    # Remove the trailing number using regular expression
    line_without_number = re.sub(r'\s*\d+$', '', line)
    # Split the line by semicolon
    parts = line_without_number.split(';')
    return parts

def extract_number_at_end(line):
    match = re.search(r'\d+$', line)
    if match:
        return int(match.group())
    else:
        return None
    
def get_high_level_symbol(line):
    blacklisted_symbols = ['entry_SYSCALL_64', 'do_syscall_64', 'do_syscall_x64','do_syscall_x64', '__x86_indirect_thunk_rax',
                           'entry_SYSCALL_64_after_hwframe', 'strcmp', 'memmove', 'memset']
    parts = split_line_remove_number(line)
    
    parts = [part.strip() for part in parts]
    
    # shrinked_parts = parts
    # if len(parts) > 12:
    #     shrinked_parts = parts[:16]
    # shrinked_str = ';'.join(shrinked_parts)
    
    for part in parts:
        part = part.strip()
        if part not in blacklisted_symbols:
            return part, parts
        
    return parts[-1], parts

def split_to_parts(line):
    parts = split_line_remove_number(line)
    parts = [part.strip() for part in parts]
    return parts


def processing_call_chain(parts, preserved_list, black_list):
    next_match_idx = 0
    
    output_parts = []
    for i, part in enumerate(parts):
        if next_match_idx < len(preserved_list):
            if part in preserved_list[next_match_idx]:
                output_parts.append(part)
                next_match_idx += 1
            else:
                continue
        else:
            if part not in black_list:
                output_parts.append(part)
                
    output_parts = shrink_parts(output_parts)
    
    # print('input:', parts)
    # print('output:', output_parts)
    
    return output_parts


def processing_PF_handler(parts):
    preserved_list = [
        {'asm_exc_page_fault'},
        {'handle_mm_fault', 'find_vma'}
    ]
    
    black_list = {'__handle_mm_fault'}
    
    next_match_idx = 0
    
    output_parts = processing_call_chain(parts, preserved_list, black_list)
    
    # print('input:', parts)
    # print('output:', output_parts)
    
    return output_parts

def processing_syscall(parts):
    syscall = ""
    for p in parts:
        if '__x64_sys' in p:
            syscall = p
            break
        
    preserved_list = [{'entry_SYSCALL_64'}, {syscall}]
    
    if "__x64_sys_munmap" in syscall:
        preserved_list.append({'__do_munmap'})
    elif "__x64_sys_brk" in syscall:
        preserved_list.append({'__do_sys_brk'})
    elif "__x64_sys_read" in syscall:
        preserved_list.append({'ksys_read'})
    
    if syscall == "":
        preserved_list = [{'entry_SYSCALL_64'}]
    
    black_list = {'__x86_indirect_thunk_rax'}
    
    return processing_call_chain(parts, preserved_list, black_list)

def shrink_parts(parts):
    shrinked_parts = parts
    LIMIT = 6
    if len(parts) > LIMIT:
        shrinked_parts = parts[:LIMIT]
    return shrinked_parts


def replace_key_function(parts):
    key_function_map = {
        'pte_offset_ecpt': 'ecpt_locate_pte',
        'get_hpt_entry': 'do_locate',
        'ecpt_search_fit_entry': 'ecpt_search',

        'pmd_offset_ecpt': 'ecpt_locate_pmd',


        'set_pte_at' : 'insert_pte',
        'ecpt_set_pte_at': 'ecpt_insert_pte',
    }
    
    for i, part in enumerate(parts):
        if part in key_function_map:
            parts[i] = key_function_map[part]
    return parts


def make_flame_human_readable(flame_folded_path: str):
    print(f"Make {flame_folded_path} human readable")
    readable_flame_path =  flame_folded_path + ".readable"
    
    with open(readable_flame_path, 'w') as readable:
        with open(flame_folded_path, 'r') as file:
            for line in file:
                # high_level_key, parts = get_high_level_symbol(line)
                parts = split_to_parts(line)
                high_level_key = parts[0]
                
                number = extract_number_at_end(line)
                # print(high_level_key)
                if  'timer' not in high_level_key:
                    if 'asm_exc_page_fault' in high_level_key:
                        parts = processing_PF_handler(parts)
                    if 'entry_SYSCALL_64' in high_level_key:
                        parts = processing_syscall(parts)
                    else:
                        parts = shrink_parts(parts)
                    parts = replace_key_function(parts)
                    print(f"{';'.join(parts).strip()} {number}", file = readable)

    return readable_flame_path

def produce_flame_graph(folded_path: str):
    flamegraph_out_path = folded_path + ".svg"
    command = f"./flamegraph.pl --width 1000 --height 18 --title \" \" {folded_path} > {flamegraph_out_path}"
    print(command)
    subprocess.run(command, shell=True, check=True)
    print("Flamegraph saved to ", flamegraph_out_path)
    
    
    return flamegraph_out_path

if __name__ == '__main__':
    folder = 'kernel_inst_loading/'
    files = [f for f in os.listdir(f'{folder}')]
    
    for folded_path in files:
        if folded_path.endswith('.folded'):
            print(folded_path)
            flame_folded_path = os.path.join(f'{folder}', folded_path)
            readable_flame_path = make_flame_human_readable(flame_folded_path)
            produce_flame_graph(readable_flame_path)
    
    # flame_folded_path = "kernel_inst/radix_never_graphbig_bfs_walk_log.bin.kern_inst.folded"
    # readable_flame_path = make_flame_human_readable(flame_folded_path)
    # produce_flame_graph(readable_flame_path)
    