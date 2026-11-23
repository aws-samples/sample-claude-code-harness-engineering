# Brief 3: merging duplicate member accounts (internal tool)

*Notes from a support and engineering catch-up. The product is Mossbank, the app that community gardens use to manage plots, members and shared tools. Mossbank and the people are made up for this exercise.*

- This one is for our own support team, not for gardeners.
- People end up with two accounts. They sign up with a work email and later a personal one, or a coordinator adds them by hand and then they sign up themselves. Support is asked to merge the two. Today Dana (support) asks engineering to run a script, and each request takes a day or two to come back.
- Dana: "a handful a week". Priya (engineering): the script log shows 31 runs between January and March.
- Wanted: a button in the support console that merges two accounts.
- Which account wins? Plot history, waiting-list place, tool loans and payment records for plot fees can all differ between the two. If both accounts are on the same waiting list, which place do they keep? Not discussed.
- Priya: with the current script a merge cannot be undone. She is nervous about a button that makes it easy.
- Dana would like members to do this themselves from their settings page one day. Ines (product): "not now".
- Who in support may do it: everyone, or team leads only? Not decided.
- No deadline. Ines wants a PRD so it can go into the next planning round.
