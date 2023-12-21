function handleAuthorDialog(id){
    const dialogElem = document.getElementById("dialog" + id);
    const showBtn = document.getElementById("show" + id);
    const closeBtn = document.getElementById("close" + id);

    showBtn.addEventListener("click", () => {
        dialogElem.showModal();
    });

    closeBtn.addEventListener("click", () => {
        dialogElem.close();
    });
}