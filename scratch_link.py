import sys

code = '''
def run_analysis():
    try:
        from openstaad import ops
        s = ops.connect()
        s.Analyze() # Block until done
        return True
    except Exception as e:
        print(f"Error running analysis: {e}")
        return False

def get_design_results(member_ids):
    """
    Given a list of member IDs, fetches their design ratio from STAAD.
    Returns a dictionary: {member_id: ratio, ...}
    """
    results = {}
    try:
        from openstaad import ops
        s = ops.connect()
        for mid in member_ids:
            try:
                ratio = s.GetMemberSteelDesignRatio(mid)
                results[mid] = ratio
            except:
                results[mid] = 0.0
    except Exception as e:
        print(f"Error getting design results: {e}")
    return results
'''

with open('app/staad_link/link.py', 'a', encoding='utf-8') as f:
    f.write(code)
