# PassFlow System - Merged Workflow

## Complete Workflow (User + Admin Combined)

```
┌──────────────────────────────────────────┐
│              START                        │
└──────────────────────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │   Welcome to PassFlow     │
        └───────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │    Check if New User?     │◄──┐
        └───────────────────────────┘   │
              YES ↙      ↘ NO           │
    ┌──────────────┐   ┌─────────────┐  │
    │   Register   │   │    Login    │  │
    │  (New User)  │   └─────────────┘  │
    └──────────────┘         ↓          │
              ↓        ┌──────────────┐  │
              └───────→│    Login     │──┤
                       └──────────────┘  │
                              ↓          │
                    ┌──────────────────┐ │
                    │  What is your    │ │
                    │      Role?       │ │
                    └──────────────────┘ │
                  STUDENT ↙    ↘ ADMIN  │
        ┌──────────────┐   ┌─────────────┐
        │  Student     │   │  Admin      │
        │  Dashboard   │   │  Dashboard  │
        └──────────────┘   └─────────────┘
              ↓                   ↓
    ┌──────────────────┐  ┌─────────────┐
    │ Complete Profile │  │ Approve     │
    │   (First Time?)  │  │ Passes      │
    └──────────────────┘  └─────────────┘
              ↓                   ↓
      ┌───────────────┐   ┌─────────────┐
      │  Create Pass  │   │  Manage     │
      └───────────────┘   │  System     │
              ↓           └─────────────┘
      ┌───────────────┐          ↓
      │ Make Payment  │  ┌─────────────┐
      └───────────────┘  │   Monitor   │
              ↓          │   Revenue   │
      ┌───────────────┐  └─────────────┘
      │ Receive Pass  │          ↓
      └───────────────┘          │
              ↓                  │
    ┌──────────────────┐         │
    │ Check for Expiry │         │
    │   Alerts         │         │
    └──────────────────┘         │
              ↓                  │
    ┌──────────────────┐         │
    │  Still Active?   │         │
    └──────────────────┘         │
      YES ↙    ↘ NO              │
   ┌────────┐ ┌──────────────┐   │
   │ Use Bus│ │  Renew Pass  │───┘
   │ Service│ └──────────────┘
   └────────┘
        ↓
┌──────────────────────────────────────────┐
│              FINISH                       │
└──────────────────────────────────────────┘
```

---

## Quick Reference

**User Path:**
1. Register (if new) → Login → Complete Profile
2. Create Pass → Make Payment → Receive Pass
3. Use Bus Service → Renew when needed

**Admin Path:**
1. Login → Dashboard
2. Approve Passes → Manage System → Monitor Revenue

---

## Key Decision Points

- **New User?** → Register first
- **Returning User?** → Login directly
- **Role?** → Student or Admin dashboard
- **Pass Expiry?** → Renew or continue using

---

✅ **Simple Workflow Complete!**

