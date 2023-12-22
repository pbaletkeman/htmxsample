function handleAuthorDialog(id){
    const dialogElem = document.getElementById("dialog" + id);
    const showBtn = document.getElementById("show" + id);
    const closeBtn = document.getElementById("close" + id);

    showBtn.addEventListener("click", () => {
        dialogElem.showModal();
    });

    closeBtn.addEventListener("click", () => {
        dialogElem.close();
        /* need to prevent the default action otherwise the URL parameters are screwed up */
        event.preventDefault();
    });
}