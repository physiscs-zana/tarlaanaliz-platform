// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-063: Rol bazlı erişim kontrolü — hem detaylı rol hem grup düzeyinde çalışır.
import { useMemo } from 'react';

import type { AuthRole, RoleGroup } from './useAuth';
import { ROLE_TO_GROUP } from './useAuth';

/**
 * Detaylı SSOT rolü veya rol grubu bazında erişim kontrolü.
 * allowedRoles: AuthRole[] — belirli roller (ör. ['COOP_OWNER', 'CENTRAL_ADMIN'])
 * allowedGroups: RoleGroup[] — grup bazlı (ör. ['farmer', 'admin'])
 */
export function useRoleGuard(
  currentRole: AuthRole | null | undefined,
  allowedRoles?: AuthRole[],
  allowedGroups?: RoleGroup[],
) {
  return useMemo(() => {
    if (!currentRole) {
      return { allowed: false, forbidden: true, requiredRoles: allowedRoles ?? [], requiredGroups: allowedGroups ?? [] };
    }

    const roleMatch = allowedRoles ? allowedRoles.includes(currentRole) : false;
    const groupMatch = allowedGroups ? allowedGroups.includes(ROLE_TO_GROUP[currentRole]) : false;
    const allowed = roleMatch || groupMatch;

    return {
      allowed,
      forbidden: !allowed,
      requiredRoles: allowedRoles ?? [],
      requiredGroups: allowedGroups ?? [],
    };
  }, [allowedGroups, allowedRoles, currentRole]);
}
